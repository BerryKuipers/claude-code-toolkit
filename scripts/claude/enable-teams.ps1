<#
.SYNOPSIS
    Enable the experimental Agent Teams feature for Claude Code.

.DESCRIPTION
    Sets CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in a Claude Code settings file.
    Idempotent: safe to run multiple times. Merges into existing JSON without overwriting.

.PARAMETER Scope
    Where to write the setting:
      "local"   -> .claude/settings.local.json  (default, gitignored)
      "project" -> .claude/settings.json        (committed)
      "user"    -> ~/.claude/settings.json      (global)

.EXAMPLE
    .\enable-teams.ps1
    .\enable-teams.ps1 -Scope project
    .\enable-teams.ps1 -Scope user
#>
param(
    [ValidateSet("local", "project", "user")]
    [string]$Scope = "local"
)

$ErrorActionPreference = "Stop"

# Determine target file
switch ($Scope) {
    "user" {
        $settingsFile = Join-Path $env:USERPROFILE ".claude" "settings.json"
    }
    "project" {
        $settingsFile = Join-Path $PWD ".claude" "settings.json"
    }
    "local" {
        $settingsFile = Join-Path $PWD ".claude" "settings.local.json"
    }
}

# Ensure directory exists
$dir = Split-Path $settingsFile -Parent
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Load or create settings
$settings = @{}
if (Test-Path $settingsFile) {
    $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json -AsHashtable
}

# Ensure env key exists
if (-not $settings.ContainsKey("env")) {
    $settings["env"] = @{}
}

# Set the flag
$settings["env"]["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"

# Write back
$json = $settings | ConvertTo-Json -Depth 10
$json | Set-Content $settingsFile -Encoding utf8

Write-Host "Agent Teams enabled in $settingsFile" -ForegroundColor Green
Write-Host ""
Write-Host "Restart Claude Code for this to take effect." -ForegroundColor Yellow
Write-Host "Usage: tell Claude to 'create an agent team' or specify teammates explicitly."
