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
    Repository owner (username or organization)
    
.PARAMETER Repo
    Repository name
    
.PARAMETER PrNumber
    Pull Request number
    
.PARAMETER DryRun
    If specified, only shows what would be resolved without actually resolving
    
.EXAMPLE
    .\resolve-pr-conversations.ps1 -Owner "BerryKuipers" -Repo "TuneScout" -PrNumber 89
    
.EXAMPLE
    .\resolve-pr-conversations.ps1 -Owner "BerryKuipers" -Repo "TuneScout" -PrNumber 89 -DryRun
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Owner,
    
    [Parameter(Mandatory = $true)]
    [string]$Repo,
    
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,
    
    [switch]$DryRun
)

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Reset = "`e[0m"

Write-Host "${Blue}Fetching review threads for PR #$PrNumber in $Owner/$Repo${Reset}"

# GraphQL query to get all review threads for the PR
$query = @"
query(`$owner: String!, `$repo: String!, `$prNumber: Int!) {
  repository(owner: `$owner, name: `$repo) {
    pullRequest(number: `$prNumber) {
      id
      title
      reviewThreads(first: 100) {
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
    # Execute the query
    $result = gh api graphql -H "X-Github-Next-Global-ID:1" -f query=$query -F owner=$Owner -F repo=$Repo -F prNumber=$PrNumber | ConvertFrom-Json
    
    if (-not $result.data.repository.pullRequest) {
        Write-Host "${Red}Pull Request #$PrNumber not found in $Owner/$Repo${Reset}"
        exit 1
    }
    
    $pr = $result.data.repository.pullRequest
    $threads = $pr.reviewThreads.nodes
    
    Write-Host "${Blue}Found $($threads.Count) total review threads${Reset}"

    # Filter for unresolved threads
    $unresolvedThreads = $threads | Where-Object { -not $_.isResolved }

    if ($unresolvedThreads.Count -eq 0) {
        Write-Host "${Green}All conversations are already resolved!${Reset}"
        exit 0
    }

    Write-Host "${Yellow}Found $($unresolvedThreads.Count) unresolved conversations${Reset}"
    
    if ($DryRun) {
        Write-Host "${Yellow}DRY RUN - Would resolve the following conversations:${Reset}"
        foreach ($thread in $unresolvedThreads) {
            $comment = $thread.comments.nodes[0]
            if ($comment) {
                Write-Host "  Thread ID: $($thread.id)"
                Write-Host "    File: $($comment.path) (line $($comment.line))"
                Write-Host "    Author: $($comment.author.login)"
                Write-Host "    Preview: $($comment.body.Substring(0, [Math]::Min(100, $comment.body.Length)))..."
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
                Write-Host "${Green}  Successfully resolved${Reset}"
                $resolvedCount++
            } else {
                Write-Host "${Red}  Failed to resolve (unknown reason)${Reset}"
                $failedCount++
            }
        }
        catch {
            Write-Host "${Red}  Failed to resolve: $($_.Exception.Message)${Reset}"
            $failedCount++
        }
        
        # Small delay to avoid rate limiting
        Start-Sleep -Milliseconds 100
    }
    
    # Summary
    Write-Host ""
    Write-Host "${Blue}Summary:${Reset}"
    Write-Host "${Green}  Resolved: $resolvedCount${Reset}"
    if ($failedCount -gt 0) {
        Write-Host "${Red}  Failed: $failedCount${Reset}"
    }
    Write-Host "${Blue}  PR: https://github.com/$Owner/$Repo/pull/$PrNumber${Reset}"

    if ($resolvedCount -gt 0) {
        Write-Host ""
        Write-Host "${Green}Successfully resolved $resolvedCount conversation(s)!${Reset}"
    }
}
catch {
    Write-Host "${Red}Error: $($_.Exception.Message)${Reset}"
    exit 1
}
