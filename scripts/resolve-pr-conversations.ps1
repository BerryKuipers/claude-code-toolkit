#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automatically resolve all unresolved conversations in a GitHub Pull Request

.DESCRIPTION
    This script uses GitHub CLI and GraphQL to:
    1. Fetch all review threads for a given PR
    2. Filter for unresolved threads
    3. Resolve them using the resolveReviewThread mutation

.PARAMETER Owner
    Repository owner (username or organization). Defaults to "BerryKuipers"

.PARAMETER Repo
    Repository name. Defaults to "SynchronicityEngine"

.PARAMETER PrNumber
    Pull Request number

.PARAMETER DryRun
    If specified, only shows what would be resolved without actually resolving

.EXAMPLE
    .\resolve-pr-conversations.ps1 -PrNumber 32

.EXAMPLE
    .\resolve-pr-conversations.ps1 -PrNumber 32 -DryRun

.EXAMPLE
    .\resolve-pr-conversations.ps1 -Owner "BerryKuipers" -Repo "SynchronicityEngine" -PrNumber 32
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$Owner,

    [Parameter(Mandatory = $false)]
    [string]$Repo,

    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [switch]$DryRun
)

# Auto-detect repo from gh CLI if not provided
if (-not $Owner -or -not $Repo) {
    try {
        $repoInfo = gh repo view --json owner,name | ConvertFrom-Json
        if (-not $Owner) { $Owner = $repoInfo.owner.login }
        if (-not $Repo) { $Repo = $repoInfo.name }
        Write-Host "${Blue}Auto-detected repo: $Owner/$Repo${Reset}"
    } catch {
        Write-Host "${Red}Error: Could not auto-detect repository. Please specify -Owner and -Repo${Reset}"
        exit 1
    }
}

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Reset = "`e[0m"

Write-Host "${Blue}Fetching review threads for PR #$PrNumber in $Owner/$Repo${Reset}"

# GraphQL query to get all review threads for the PR (with pagination support)
$query = @"
query(`$owner: String!, `$repo: String!, `$prNumber: Int!, `$after: String) {
  repository(owner: `$owner, name: `$repo) {
    pullRequest(number: `$prNumber) {
      id
      title
      reviewThreads(first: 100, after: `$after) {
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              path
              line
              body
              author {
                login
              }
            }
          }
        }
      }
    }
  }
}
"@

try {
    # Fetch all review threads with pagination
    $allThreads = @()
    $after = $null
    $hasNextPage = $true

    while ($hasNextPage) {
        # Execute the query with pagination cursor
        if ($after) {
            $result = gh api graphql -H "X-Github-Next-Global-ID:1" -f query=$query -F owner=$Owner -F repo=$Repo -F prNumber=$PrNumber -F after=$after | ConvertFrom-Json
        } else {
            $result = gh api graphql -H "X-Github-Next-Global-ID:1" -f query=$query -F owner=$Owner -F repo=$Repo -F prNumber=$PrNumber | ConvertFrom-Json
        }

        if (-not $result.data.repository.pullRequest) {
            Write-Host "${Red}❌ Pull Request #$PrNumber not found in $Owner/$Repo${Reset}"
            exit 1
        }

        $pr = $result.data.repository.pullRequest
        $allThreads += $pr.reviewThreads.nodes

        $hasNextPage = $pr.reviewThreads.pageInfo.hasNextPage
        $after = $pr.reviewThreads.pageInfo.endCursor
    }

    $threads = $allThreads
    Write-Host "${Blue}Found $($threads.Count) total review threads${Reset}"

    # Filter for unresolved threads
    $unresolvedThreads = $threads | Where-Object { -not $_.isResolved }

    if ($unresolvedThreads.Count -eq 0) {
        Write-Host "${Green}✅ All conversations are already resolved!${Reset}"
        exit 0
    }

    Write-Host "${Yellow}Found $($unresolvedThreads.Count) unresolved conversations${Reset}"

    if ($DryRun) {
        Write-Host "${Yellow}🔍 DRY RUN - Would resolve the following conversations:${Reset}"
        foreach ($thread in $unresolvedThreads) {
            if ($thread.comments.nodes.Count -eq 0) {
                Write-Host "${Yellow}  Skipping thread $($thread.id) - no comments${Reset}"
                continue
            }
            $comment = $thread.comments.nodes[0]
            if ($comment) {
                Write-Host "  Thread ID: $($thread.id)"
                Write-Host "    File: $($comment.path) (line $($comment.line))"
                Write-Host "    Author: $($comment.author.login)"
                $preview = if ($comment.body) { $comment.body.Substring(0, [Math]::Min(100, $comment.body.Length)) } else { "(empty)" }
                Write-Host "    Preview: $preview..."
                Write-Host ""
            }
        }
        Write-Host "${Yellow}Run without -DryRun to actually resolve these conversations${Reset}"
        exit 0
    }

    # Resolve each unresolved thread
    $resolvedCount = 0
    $failedCount = 0

    foreach ($thread in $unresolvedThreads) {
        if ($thread.comments.nodes.Count -eq 0) {
            Write-Host "${Yellow}Skipping thread $($thread.id) - no comments${Reset}"
            continue
        }

        $comment = $thread.comments.nodes[0]
        $threadId = $thread.id

        Write-Host "${Blue}Resolving thread: $($comment.path):$($comment.line)${Reset}"

        # GraphQL mutation to resolve the thread
        $resolveMutation = @"
mutation(`$threadId: ID!) {
  resolveReviewThread(input: {threadId: `$threadId}) {
    thread {
      id
      isResolved
    }
  }
}
"@

        try {
            $resolveResult = gh api graphql -H "X-Github-Next-Global-ID:1" -f query=$resolveMutation -F threadId=$threadId | ConvertFrom-Json

            if ($resolveResult.data.resolveReviewThread.thread.isResolved) {
                Write-Host "${Green}  ✓ Successfully resolved${Reset}"
                $resolvedCount++
            } else {
                Write-Host "${Red}  ✗ Failed to resolve (unknown reason)${Reset}"
                $failedCount++
            }
        }
        catch {
            Write-Host "${Red}  ✗ Failed to resolve: $($_.Exception.Message)${Reset}"
            $failedCount++
        }

        # Small delay to avoid rate limiting
        Start-Sleep -Milliseconds 100
    }

    # Summary
    Write-Host ""
    Write-Host "${Blue}═══════════════════════════════════════${Reset}"
    Write-Host "${Blue}Summary:${Reset}"
    Write-Host "${Green}  ✓ Resolved: $resolvedCount${Reset}"
    if ($failedCount -gt 0) {
        Write-Host "${Red}  ✗ Failed: $failedCount${Reset}"
    }
    Write-Host "${Blue}  🔗 PR: https://github.com/$Owner/$Repo/pull/$PrNumber${Reset}"
    Write-Host "${Blue}═══════════════════════════════════════${Reset}"

    if ($resolvedCount -gt 0) {
        Write-Host ""
        Write-Host "${Green}🎉 Successfully resolved $resolvedCount conversation(s)!${Reset}"
    }
}
catch {
    Write-Host "${Red}❌ Error: $($_.Exception.Message)${Reset}"
    exit 1
}
