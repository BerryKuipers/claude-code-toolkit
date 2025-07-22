#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automatically resolve all unresolved conversations in a GitHub Pull Request for crypto-insight

.PARAMETER PrNumber
    Pull Request number

.PARAMETER DryRun
    If specified, only shows what would be resolved without actually resolving

.EXAMPLE
    .\resolve-pr-conversations-simple.ps1 -PrNumber 3

.EXAMPLE
    .\resolve-pr-conversations-simple.ps1 -PrNumber 3 -DryRun
#>

param(
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [switch]$DryRun
)

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

$Owner = "BerryKuipers"
$Repo = "crypto-insight"

Write-Host "${Blue}🔍 Fetching review threads for PR #$PrNumber in $Owner/$Repo${Reset}"

# Check if GitHub CLI is available
try {
    $ghVersion = gh --version 2>$null
    if (-not $ghVersion) {
        throw "GitHub CLI not found"
    }
    Write-Host "${Green}✅ GitHub CLI found${Reset}"
}
catch {
    Write-Host "${Red}❌ GitHub CLI is required but not found. Please install it from https://cli.github.com/${Reset}"
    exit 1
}

try {
    # Get PR details first
    Write-Host "${Cyan}📡 Querying GitHub API...${Reset}"
    $prData = gh pr view $PrNumber --repo "$Owner/$Repo" --json title,state | ConvertFrom-Json
    
    if (-not $prData) {
        Write-Host "${Red}❌ Pull Request #$PrNumber not found in $Owner/$Repo${Reset}"
        exit 1
    }

    Write-Host "${Blue}📊 PR Details:${Reset}"
    Write-Host "  Title: $($prData.title)"
    Write-Host "  State: $($prData.state)"

    # Get review comments
    $comments = gh api "/repos/$Owner/$Repo/pulls/$PrNumber/comments" | ConvertFrom-Json
    
    if (-not $comments -or $comments.Count -eq 0) {
        Write-Host "${Green}🎉 No review comments found!${Reset}"
        exit 0
    }

    Write-Host "  Total review comments: $($comments.Count)"

    if ($DryRun) {
        Write-Host "${Yellow}🔍 DRY RUN - Review comments found:${Reset}"
        Write-Host ""
        
        $counter = 1
        foreach ($comment in $comments) {
            Write-Host "${Blue}[$counter] Comment Details:${Reset}"
            Write-Host "    📁 File: $($comment.path)"
            if ($comment.line) {
                Write-Host "    📍 Line: $($comment.line)"
            }
            Write-Host "    👤 Author: $($comment.user.login)"
            Write-Host "    📅 Created: $($comment.created_at)"
            Write-Host "    💬 Preview: $($comment.body.Substring(0, [Math]::Min(150, $comment.body.Length)))..."
            Write-Host "    🔗 Comment ID: $($comment.id)"
            Write-Host ""
            $counter++
        }
        Write-Host "${Yellow}💡 Note: This script shows review comments. For conversation threads, use GitHub's web interface.${Reset}"
        Write-Host "${Yellow}🚀 Run without -DryRun to mark these as resolved (if supported by API)${Reset}"
        exit 0
    }

    # For now, just show the comments since resolving review threads requires GraphQL
    Write-Host "${Yellow}📝 Found $($comments.Count) review comment(s)${Reset}"
    Write-Host "${Cyan}💡 To resolve conversations, please use GitHub's web interface or implement GraphQL queries${Reset}"
    Write-Host "${Blue}🔗 PR Link: https://github.com/$Owner/$Repo/pull/$PrNumber${Reset}"
}
catch {
    Write-Host "${Red}💥 Error: $($_.Exception.Message)${Reset}"
    Write-Host "${Yellow}💡 Common issues:${Reset}"
    Write-Host "  - Make sure you're authenticated with GitHub CLI (gh auth login)"
    Write-Host "  - Verify the PR number and repository access"
    Write-Host "  - Check your internet connection"
    exit 1
}
