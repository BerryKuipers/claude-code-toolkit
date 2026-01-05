# Reflection Stop Hook - PowerShell Version
# Called on Stop event to log reflection candidates
#
# This hook:
# 1. Checks if reflection logging is enabled for this repo
# 2. Appends a minimal candidate entry to reflection-candidates.jsonl
# 3. Prints a short notification
#
# CRITICAL: This hook NEVER modifies skills/rules or commits. It only logs.

param()

$ErrorActionPreference = "SilentlyContinue"

# Configuration
$ProjectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }
$ConfigFile = Join-Path $ProjectDir ".claude/config.yml"
$StateDir = Join-Path $ProjectDir ".claude/state"
$CandidatesFile = Join-Path $StateDir "reflection-candidates.jsonl"

# Check if reflection is enabled in config.yml
if (-not (Test-Path $ConfigFile)) {
    exit 0
}

$ConfigContent = Get-Content $ConfigFile -Raw
if ($ConfigContent -notmatch 'reflection:\s*\r?\n\s*enabled:\s*true') {
    exit 0
}

# Ensure state directory exists
if (-not (Test-Path $StateDir)) {
    New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
}

# Generate session token from cwd + timestamp
$SessionHash = [System.Security.Cryptography.SHA256]::Create()
$TokenBytes = $SessionHash.ComputeHash([System.Text.Encoding]::UTF8.GetBytes("$ProjectDir-$(Get-Date -Format 'yyyyMMdd')"))
$SessionToken = [System.BitConverter]::ToString($TokenBytes).Replace("-", "").Substring(0, 16).ToLower()

# Get current date and generate ID
$Today = Get-Date -Format "yyyyMMdd"
$Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Count existing candidates for today to generate sequential ID
$ExistingCount = 0
if (Test-Path $CandidatesFile) {
    $ExistingCount = (Get-Content $CandidatesFile | Where-Object { $_ -match "refl-$Today" }).Count
}
$SeqNum = ($ExistingCount + 1).ToString().PadLeft(3, '0')
$CandidateId = "refl-$Today-$SeqNum"

# Get git info for context
$Branch = & git branch --show-current 2>$null
if (-not $Branch) { $Branch = "unknown" }

$RecentCommit = & git log -1 --pretty=format:"%h|%s" 2>$null
if ($RecentCommit) {
    $CommitParts = $RecentCommit -split '\|', 2
    $CommitHash = $CommitParts[0]
    $CommitMsg = $CommitParts[1]
} else {
    $CommitHash = ""
    $CommitMsg = ""
}

# Create minimal candidate entry
$Candidate = @{
    id = $CandidateId
    timestamp = $Timestamp
    session_token = $SessionToken
    type = "session_end"
    confidence = "LOW"
    source = "stop_hook"
    description = "Session ended on branch: $Branch"
    evidence = @()
    proposed_rule = ""
    status = "pending"
    context = @{
        branch = $Branch
        recent_commit = $CommitHash
        commit_message = $CommitMsg
    }
}

# Convert to JSON (single line, no pretty print)
$JsonLine = $Candidate | ConvertTo-Json -Compress -Depth 10

# Append to candidates file
Add-Content -Path $CandidatesFile -Value $JsonLine

# Print notification
Write-Host ""
Write-Host "-------------------------------------------"
Write-Host " Reflection candidate logged: $CandidateId"
Write-Host " Branch: $Branch"
Write-Host " Run /reflect to analyze patterns"
Write-Host "-------------------------------------------"

exit 0
