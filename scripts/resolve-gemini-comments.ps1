#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Resolve Gemini code review comments for crypto-insight

.DESCRIPTION
    This script helps resolve Gemini AI code review comments by:
    1. Showing all unresolved Gemini comments
    2. Optionally resolving them all at once
    3. Providing a summary of what was resolved

.PARAMETER PrNumber
    Pull Request number (default: 3)

.PARAMETER DryRun
    If specified, only shows what would be resolved without actually resolving

.PARAMETER AutoResolve
    If specified, automatically resolves all Gemini comments without confirmation

.EXAMPLE
    .\resolve-gemini-comments.ps1

.EXAMPLE
    .\resolve-gemini-comments.ps1 -PrNumber 3 -DryRun

.EXAMPLE
    .\resolve-gemini-comments.ps1 -PrNumber 3 -AutoResolve
#>

param(
    [Parameter(Mandatory = $false)]
    [int]$PrNumber = 3,

    [switch]$DryRun,
    [switch]$AutoResolve
)

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Magenta = "`e[35m"
$Reset = "`e[0m"

Write-Host "${Magenta}🤖 Gemini Comment Resolver for crypto-insight${Reset}"
Write-Host "${Blue}📋 Processing PR #$PrNumber${Reset}"
Write-Host ""

# Check if the main script exists
$scriptPath = ".\scripts\resolve-pr-conversations.ps1"
if (-not (Test-Path $scriptPath)) {
    Write-Host "${Red}❌ Main script not found: $scriptPath${Reset}"
    exit 1
}

try {
    if ($DryRun) {
        Write-Host "${Yellow}🔍 DRY RUN - Checking for Gemini comments...${Reset}"
        & $scriptPath -Owner "BerryKuipers" -Repo "crypto-insight" -PrNumber $PrNumber -DryRun
    }
    elseif ($AutoResolve) {
        Write-Host "${Yellow}⚡ AUTO-RESOLVE mode - Resolving all Gemini comments...${Reset}"
        & $scriptPath -Owner "BerryKuipers" -Repo "crypto-insight" -PrNumber $PrNumber
    }
    else {
        Write-Host "${Cyan}📊 Checking current status...${Reset}"
        & $scriptPath -Owner "BerryKuipers" -Repo "crypto-insight" -PrNumber $PrNumber -DryRun
        
        Write-Host ""
        Write-Host "${Yellow}❓ Do you want to resolve all Gemini comments? (y/N)${Reset}" -NoNewline
        $confirmation = Read-Host " "
        
        if ($confirmation -eq "y" -or $confirmation -eq "Y") {
            Write-Host "${Green}🚀 Resolving comments...${Reset}"
            & $scriptPath -Owner "BerryKuipers" -Repo "crypto-insight" -PrNumber $PrNumber
        }
        else {
            Write-Host "${Yellow}🛑 Operation cancelled${Reset}"
        }
    }
    
    Write-Host ""
    Write-Host "${Green}✨ Gemini comment resolution completed!${Reset}"
    Write-Host "${Cyan}💡 Next steps:${Reset}"
    Write-Host "  1. Review the resolved comments on GitHub"
    Write-Host "  2. Address any remaining code quality issues"
    Write-Host "  3. Run tests: ${Yellow}python -m pytest tests/ -v${Reset}"
    Write-Host "  4. Check dashboard: ${Yellow}streamlit run dashboard.py${Reset}"
    Write-Host ""
    Write-Host "${Blue}🔗 PR Link: https://github.com/BerryKuipers/crypto-insight/pull/$PrNumber${Reset}"
}
catch {
    Write-Host "${Red}💥 Error: $($_.Exception.Message)${Reset}"
    exit 1
}
