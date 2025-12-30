# Loop Controller Hook - PowerShell Version
# Called on Stop event to manage loop state and safety limits
#
# This hook:
# 1. Checks if an active loop exists for this repo
# 2. Enforces max_iterations safety limit
# 3. Detects completion markers and disables loop when done
# 4. Persists state for cross-session resumption

param()

$ErrorActionPreference = "SilentlyContinue"

# Configuration
$ProjectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { Get-Location }
$StateFile = Join-Path $ProjectDir ".claude/state/loop.local.json"
$LogFile = Join-Path $ProjectDir ".claude/state/loop.log"

# Silent exit if no state file exists
if (-not (Test-Path $StateFile)) {
    exit 0
}

# Read state file
try {
    $State = Get-Content $StateFile -Raw | ConvertFrom-Json
} catch {
    Add-Content $LogFile "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') - Failed to parse state file: $_"
    exit 0
}

# Check if loop is enabled
if ($State.enabled -ne $true) {
    exit 0
}

# Load loop configuration with defaults
$MaxIterations = if ($State.max_iterations) { [int]$State.max_iterations } else { 20 }
$CurrentIteration = if ($State.iteration) { [int]$State.iteration } else { 1 }
$CompletionPromise = if ($State.completion_promise) { $State.completion_promise } else { "DONE" }
$SessionToken = $State.session_token
$StateCwd = $State.cwd
$Task = $State.original_arguments

# Session scoping: verify we're in the same repo
$CurrentCwd = (Get-Location).Path
if ($StateCwd -and ($StateCwd -ne $CurrentCwd)) {
    Add-Content $LogFile "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') - Loop state from different directory ($StateCwd), ignoring"
    exit 0
}

$Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Function to disable loop
function Disable-Loop {
    param([string]$Reason)

    $State.enabled = $false
    $State | Add-Member -NotePropertyName "disabled_reason" -NotePropertyValue $Reason -Force
    $State | Add-Member -NotePropertyName "disabled_at" -NotePropertyValue $Timestamp -Force

    $State | ConvertTo-Json -Depth 10 | Set-Content $StateFile
    Add-Content $LogFile "$Timestamp - Loop disabled: $Reason"
}

# Function to increment iteration
function Step-Iteration {
    $NewIteration = $CurrentIteration + 1

    $State.iteration = $NewIteration
    $State | Add-Member -NotePropertyName "updated_at" -NotePropertyValue $Timestamp -Force

    $State | ConvertTo-Json -Depth 10 | Set-Content $StateFile
    Add-Content $LogFile "$Timestamp - Iteration incremented to $NewIteration"

    return $NewIteration
}

# Check 1: Max iterations safety limit
if ($CurrentIteration -ge $MaxIterations) {
    Disable-Loop "Max iterations ($MaxIterations) reached"

    Write-Host ""
    Write-Host "======================================"
    Write-Host " LOOP HARD STOP - MAX ITERATIONS"
    Write-Host "======================================"
    Write-Host "Task: $Task"
    Write-Host "Iterations completed: $CurrentIteration"
    Write-Host "Status: Incomplete - manual intervention may be needed"
    Write-Host ""
    Write-Host "To resume: /loop $Task"
    Write-Host "To check status: Get-Content $StateFile | ConvertFrom-Json"
    Write-Host "======================================"
    exit 0
}

# Check 2: Look for completion marker
$DoneDetected = $false

# Method 1: Check environment variable (if Claude Code provides it)
if ($env:CLAUDE_SESSION_OUTPUT) {
    if ($env:CLAUDE_SESSION_OUTPUT -match "<promise>$([regex]::Escape($CompletionPromise))</promise>") {
        $DoneDetected = $true
        Add-Content $LogFile "$Timestamp - Completion marker found in session output"
    }
}

# Method 2: Check if done flag is set in state
if ($State.done -eq $true) {
    $DoneDetected = $true
    Add-Content $LogFile "$Timestamp - Done flag set in state file"
}

if ($DoneDetected) {
    Disable-Loop "Task completed (promise marker detected)"

    Write-Host ""
    Write-Host "======================================"
    Write-Host " LOOP COMPLETE"
    Write-Host "======================================"
    Write-Host "Task: $Task"
    Write-Host "Iterations: $CurrentIteration"
    Write-Host "Status: SUCCESS"
    Write-Host "======================================"
    exit 0
}

# Check 3: No completion detected - prepare for next iteration
$NextIteration = Step-Iteration

Write-Host ""
Write-Host "======================================"
Write-Host " LOOP ITERATION $CurrentIteration COMPLETE"
Write-Host "======================================"
Write-Host "Task: $Task"
Write-Host "Next iteration: $NextIteration / $MaxIterations"
Write-Host ""
Write-Host "Loop will continue on next session start."
Write-Host "To stop: /loop-stop"
Write-Host "======================================"

# Write continuation prompt for SessionStart hook to pick up
$ContinuationFile = Join-Path $ProjectDir ".claude/state/loop.continue"
$Continuation = @{
    continue_loop = $true
    iteration = $NextIteration
    task = $Task
    promise = $CompletionPromise
    remaining_iterations = $MaxIterations - $CurrentIteration
}
$Continuation | ConvertTo-Json | Set-Content $ContinuationFile

exit 0
