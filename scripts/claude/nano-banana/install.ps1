<#
.SYNOPSIS
    Install the nano-banana-pro image generation plugin for Claude Code.

.DESCRIPTION
    Checks prerequisites (GEMINI_API_KEY, uv), prints the exact Claude Code
    commands to install the plugin, and optionally persists the API key
    in .claude/settings.local.json.

.PARAMETER PersistKey
    If set, writes GEMINI_API_KEY to .claude/settings.local.json so Claude Code
    sessions always have it available.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -PersistKey
#>
param(
    [switch]$PersistKey
)

$ErrorActionPreference = "Stop"

Write-Host "=== nano-banana-pro Plugin Installer ===" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
$hasKey = $false
$hasUv = $false

# 1. Check GEMINI_API_KEY
if ($env:GEMINI_API_KEY) {
    Write-Host "[OK] GEMINI_API_KEY is set" -ForegroundColor Green
    $hasKey = $true
} else {
    Write-Host "[WARN] GEMINI_API_KEY is not set in your environment" -ForegroundColor Yellow
    Write-Host "       Get one at: https://aistudio.google.com/apikey" -ForegroundColor Yellow
    Write-Host "       Then:  `$env:GEMINI_API_KEY = 'your-key-here'" -ForegroundColor Yellow
}

# 2. Check uv (Python package manager)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "[OK] uv is installed" -ForegroundColor Green
    $hasUv = $true
} else {
    Write-Host "[WARN] uv (Python package manager) not found" -ForegroundColor Yellow
    Write-Host "       Install: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
}

Write-Host ""

# Print installation commands
Write-Host "=== Run these commands in Claude Code ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  /plugin marketplace add https://github.com/buildatscale-tv/claude-code-plugins" -ForegroundColor White
Write-Host "  /plugin install nano-banana-pro@buildatscale-claude-code" -ForegroundColor White
Write-Host ""
Write-Host "Then use: /nano-banana-pro:generate a cat in a spacesuit" -ForegroundColor Gray
Write-Host ""

# Optionally persist GEMINI_API_KEY in settings.local.json
if ($PersistKey) {
    if (-not $env:GEMINI_API_KEY) {
        Write-Error "Cannot persist key: GEMINI_API_KEY is not set. Set it first with `$env:GEMINI_API_KEY = 'your-key'"
        exit 1
    }

    $claudeDir = Join-Path $PWD ".claude"
    if (-not (Test-Path $claudeDir)) {
        New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    }

    $settingsFile = Join-Path $claudeDir "settings.local.json"
    $settings = @{}
    if (Test-Path $settingsFile) {
        $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json -AsHashtable
    }

    if (-not $settings.ContainsKey("env")) {
        $settings["env"] = @{}
    }
    $settings["env"]["GEMINI_API_KEY"] = $env:GEMINI_API_KEY

    $json = $settings | ConvertTo-Json -Depth 10
    $json | Set-Content $settingsFile -Encoding utf8

    Write-Host "GEMINI_API_KEY persisted in $settingsFile" -ForegroundColor Green
    Write-Host "(This file is gitignored by Claude Code automatically)" -ForegroundColor Gray
} else {
    Write-Host "=== To persist GEMINI_API_KEY locally ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option A: Run this script with -PersistKey flag:" -ForegroundColor Gray
    Write-Host "  .\install.ps1 -PersistKey" -ForegroundColor White
    Write-Host ""
    Write-Host "Option B: Manually add to .claude/settings.local.json:" -ForegroundColor Gray
    Write-Host '  { "env": { "GEMINI_API_KEY": "your-key-here" } }' -ForegroundColor White
    Write-Host ""
}

if (-not $hasKey -or -not $hasUv) {
    Write-Host "Fix the warnings above before using the plugin." -ForegroundColor Yellow
}
