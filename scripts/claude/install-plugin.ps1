<#
.SYNOPSIS
    Registers the claude-code-toolkit as a plugin marketplace in a consuming repo.

.DESCRIPTION
    Detects the toolkit submodule path (or accepts it as a parameter) and adds
    an extraKnownMarketplaces entry to the consuming repo's .claude/settings.json.
    Idempotent: safe to run multiple times.

.PARAMETER ToolkitPath
    Path to the toolkit submodule relative to the consuming repo root.
    If not provided, auto-detects from .gitmodules.

.PARAMETER Scope
    Where to write the setting: "project" (.claude/settings.json) or "local" (.claude/settings.local.json).
    Default: "project"

.EXAMPLE
    .\install-plugin.ps1
    .\install-plugin.ps1 -ToolkitPath ".claude-toolkit"
    .\install-plugin.ps1 -Scope local
#>
param(
    [string]$ToolkitPath = "",
    [ValidateSet("project", "local")]
    [string]$Scope = "project"
)

$ErrorActionPreference = "Stop"

# Auto-detect toolkit path from .gitmodules
if (-not $ToolkitPath) {
    $gitmodules = Join-Path $PWD ".gitmodules"
    if (Test-Path $gitmodules) {
        $content = Get-Content $gitmodules -Raw
        if ($content -match 'path\s*=\s*(.+claude-code-toolkit.*)') {
            $ToolkitPath = $Matches[1].Trim()
            Write-Host "Auto-detected toolkit at: $ToolkitPath" -ForegroundColor Green
        }
    }
    if (-not $ToolkitPath) {
        # Fallback: scan for marker file
        $candidates = Get-ChildItem -Path $PWD -Recurse -Depth 3 -Filter "plugin.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -like "*claude-plugin*" -and (Get-Content $_.FullName -Raw) -match '"claude-code-toolkit"' }
        if ($candidates) {
            $ToolkitPath = (Split-Path (Split-Path $candidates[0].DirectoryName -Parent) -Leaf)
            # Get relative path from repo root
            $ToolkitPath = [System.IO.Path]::GetRelativePath($PWD, (Split-Path $candidates[0].DirectoryName -Parent))
            Write-Host "Found toolkit at: $ToolkitPath" -ForegroundColor Green
        } else {
            Write-Error "Could not auto-detect toolkit path. Pass -ToolkitPath explicitly."
            exit 1
        }
    }
}

# Verify toolkit exists
$fullToolkitPath = Join-Path $PWD $ToolkitPath
if (-not (Test-Path (Join-Path $fullToolkitPath ".claude-plugin" "marketplace.json"))) {
    Write-Error "Toolkit marketplace not found at $fullToolkitPath/.claude-plugin/marketplace.json"
    exit 1
}

# Determine target settings file
$claudeDir = Join-Path $PWD ".claude"
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
}

$settingsFile = if ($Scope -eq "local") {
    Join-Path $claudeDir "settings.local.json"
} else {
    Join-Path $claudeDir "settings.json"
}

# Load or create settings
$settings = @{}
if (Test-Path $settingsFile) {
    $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json -AsHashtable
}

# Ensure extraKnownMarketplaces exists
if (-not $settings.ContainsKey("extraKnownMarketplaces")) {
    $settings["extraKnownMarketplaces"] = @{}
}

# Add/update marketplace entry
$marketplaceName = "berry-toolkit"
$settings["extraKnownMarketplaces"][$marketplaceName] = @{
    source = @{
        source = "directory"
        path   = $ToolkitPath
    }
}

# Write back with proper formatting
$json = $settings | ConvertTo-Json -Depth 10
$json | Set-Content $settingsFile -Encoding utf8

Write-Host ""
Write-Host "Marketplace '$marketplaceName' registered in $settingsFile" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run:  claude --plugin-dir $ToolkitPath"
Write-Host "  2. Or in Claude Code:  /plugin marketplace add ./$ToolkitPath"
Write-Host "  3. Then:  /plugin install claude-code-toolkit@berry-toolkit"
