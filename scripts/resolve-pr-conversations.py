#!/usr/bin/env python3
"""
Automatically resolve all unresolved conversations in a GitHub Pull Request
Python equivalent of resolve-pr-conversations.ps1 using GitHub API
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_info(message: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def print_success(message: str) -> None:
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def print_warning(message: str) -> None:
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


class GitHubAPI:
    """GitHub API client for PR conversation management"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def graphql_query(self, query: str, variables: Dict) -> Dict:
        """Execute a GraphQL query"""
        url = "https://api.github.com/graphql"
        headers = {
            **self.headers,
            "X-Github-Next-Global-ID": "1"
        }
        
        response = requests.post(
            url,
            headers=headers,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        return response.json()
    
    def get_pr_review_threads(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get all review threads for a PR"""
        query = """
        query($owner: String!, $repo: String!, $prNumber: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $prNumber) {
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
        """
        
        variables = {
            "owner": owner,
            "repo": repo,
            "prNumber": pr_number
        }
        
        result = self.graphql_query(query, variables)
        
        if not result.get("data", {}).get("repository", {}).get("pullRequest"):
            raise ValueError(f"Pull Request #{pr_number} not found in {owner}/{repo}")
        
        return result["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    
    def resolve_review_thread(self, thread_id: str) -> bool:
        """Resolve a review thread"""
        mutation = """
        mutation($threadId: ID!) {
          resolveReviewThread(input: {threadId: $threadId}) {
            thread {
              id
              isResolved
            }
          }
        }
        """
        
        variables = {"threadId": thread_id}
        
        try:
            result = self.graphql_query(mutation, variables)
            return result["data"]["resolveReviewThread"]["thread"]["isResolved"]
        except Exception as e:
            print_error(f"Failed to resolve thread {thread_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Automatically resolve all unresolved conversations in a GitHub Pull Request"
    )
    parser.add_argument("-o", "--owner", required=True, help="Repository owner (username or organization)")
    parser.add_argument("-r", "--repo", required=True, help="Repository name")
    parser.add_argument("-p", "--pr-number", type=int, required=True, help="Pull Request number")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Show what would be resolved without actually resolving")
    parser.add_argument("-t", "--token", help="GitHub token (defaults to GITHUB_TOKEN env var)")
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print_error("GitHub token is required. Set GITHUB_TOKEN environment variable or use --token")
        sys.exit(1)
    
    try:
        # Initialize GitHub API client
        github = GitHubAPI(token)
        
        print_info(f"Fetching review threads for PR #{args.pr_number} in {args.owner}/{args.repo}")
        
        # Get all review threads
        threads = github.get_pr_review_threads(args.owner, args.repo, args.pr_number)
        total_threads = len(threads)
        
        print_info(f"Found {total_threads} total review threads")
        
        # Filter for unresolved threads
        unresolved_threads = [thread for thread in threads if not thread["isResolved"]]
        unresolved_count = len(unresolved_threads)
        
        if unresolved_count == 0:
            print_success("All conversations are already resolved!")
            return
        
        print_warning(f"Found {unresolved_count} unresolved conversations")
        
        if args.dry_run:
            print_warning("DRY RUN - Would resolve the following conversations:")
            for thread in unresolved_threads:
                comment = thread["comments"]["nodes"][0] if thread["comments"]["nodes"] else {}
                path = comment.get("path", "unknown")
                line = comment.get("line", "?")
                author = comment.get("author", {}).get("login", "unknown")
                body = comment.get("body", "")
                preview = body[:100] + "..." if len(body) > 100 else body
                
                print(f"  Thread ID: {thread['id']}")
                print(f"    File: {path} (line {line})")
                print(f"    Author: {author}")
                print(f"    Preview: {preview}")
                print()
            
            print_warning("Run without --dry-run to actually resolve these conversations")
            return
        
        # Resolve each unresolved thread
        resolved_count = 0
        failed_count = 0
        
        for thread in unresolved_threads:
            comment = thread["comments"]["nodes"][0] if thread["comments"]["nodes"] else {}
            path = comment.get("path", "unknown")
            line = comment.get("line", "?")
            thread_id = thread["id"]
            
            print_info(f"Resolving thread: {path}:{line}")
            
            if github.resolve_review_thread(thread_id):
                print_success("  Successfully resolved")
                resolved_count += 1
            else:
                print_error("  Failed to resolve")
                failed_count += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        # Summary
        print()
        print_info("Summary:")
        print_success(f"  Resolved: {resolved_count}")
        if failed_count > 0:
            print_error(f"  Failed: {failed_count}")
        print_info(f"  PR: https://github.com/{args.owner}/{args.repo}/pull/{args.pr_number}")
        
        if resolved_count > 0:
            print()
            print_success(f"Successfully resolved {resolved_count} conversation(s)!")
    
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
