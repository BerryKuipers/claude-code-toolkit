#!/usr/bin/env python3
"""
Validate Git Hygiene - Check commit messages, branch names, and repository hygiene
"""

import subprocess
import re
import json
import sys
from pathlib import Path


# Conventional commit types
VALID_COMMIT_TYPES = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'perf', 'ci', 'build', 'revert']

# Sensitive file patterns to warn about
SENSITIVE_PATTERNS = ['.env', 'credentials', 'secrets', '.pem', '.key', 'password', 'token']


def is_git_repo():
    """Check if current directory is a git repository"""
    return Path('.git').exists() or subprocess.run(
        ['git', 'rev-parse', '--git-dir'],
        capture_output=True
    ).returncode == 0


def get_current_branch():
    """Get current branch name"""
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None


def validate_branch_name(branch_name):
    """Validate branch naming convention"""
    if not branch_name:
        return {"valid": False, "problem": "No branch found"}

    # Check for valid patterns: feat/*, fix/*, chore/*, etc.
    valid_patterns = [
        r'^feat/[\w-]+',
        r'^fix/[\w-]+',
        r'^chore/[\w-]+',
        r'^refactor/[\w-]+',
        r'^test/[\w-]+',
        r'^docs/[\w-]+',
        r'^hotfix/[\w-]+',
        r'^release/[\w-]+',
        r'^claude/[\w-]+'  # Claude Code branches
    ]

    for pattern in valid_patterns:
        if re.match(pattern, branch_name):
            return {"valid": True, "pattern": pattern}

    # Check for main/master/development (always valid)
    if branch_name in ['main', 'master', 'development', 'develop']:
        return {"valid": True, "pattern": "main branch"}

    return {
        "valid": False,
        "pattern": None,
        "problem": "Should follow pattern: feat/*, fix/*, chore/*, etc."
    }


def get_recent_commits(count=10):
    """Get recent commit messages"""
    result = subprocess.run(
        ['git', 'log', f'-{count}', '--pretty=format:%H|%s'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.split('\n'):
        if '|' in line:
            commit_hash, message = line.split('|', 1)
            commits.append({"hash": commit_hash[:7], "message": message})

    return commits


def validate_commit_message(message):
    """Validate commit message follows conventions"""
    # Conventional Commits pattern: type(scope): description
    conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^\)]+\))?:\s*.+'

    if re.match(conventional_pattern, message):
        return {"valid": True}

    # Check for common issues
    if len(message) > 72:
        return {"valid": False, "problem": "Subject line too long (>72 chars)"}

    if not any(message.startswith(t) for t in VALID_COMMIT_TYPES):
        return {"valid": False, "problem": f"Missing type prefix ({'/'.join(VALID_COMMIT_TYPES[:5])}/etc)"}

    if ':' not in message:
        return {"valid": False, "problem": "Missing colon after type"}

    return {"valid": False, "problem": "Does not follow Conventional Commits format"}


def check_working_directory():
    """Check for uncommitted changes"""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return "unknown"

    return "clean" if not result.stdout.strip() else "dirty"


def find_sensitive_files():
    """Find untracked files that might be sensitive"""
    result = subprocess.run(
        ['git', 'ls-files', '--others', '--exclude-standard'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    untracked_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

    sensitive = []
    for file in untracked_files:
        if any(pattern in file.lower() for pattern in SENSITIVE_PATTERNS):
            sensitive.append(file)

    return sensitive


def validate_git_hygiene():
    """Main validation function"""
    if not is_git_repo():
        return {
            "status": "error",
            "error": "Not a git repository",
            "suggestion": "Initialize git: git init"
        }

    # Get current branch
    branch_name = get_current_branch()
    branch_validation = validate_branch_name(branch_name)

    # Validate recent commits
    commits = get_recent_commits()
    valid_commits = 0
    invalid_commits = 0
    commit_issues = []

    for commit in commits:
        validation = validate_commit_message(commit["message"])
        if validation["valid"]:
            valid_commits += 1
        else:
            invalid_commits += 1
            commit_issues.append({
                "commit": commit["hash"],
                "message": commit["message"][:50] + "..." if len(commit["message"]) > 50 else commit["message"],
                "problem": validation.get("problem", "Invalid format")
            })

    # Check working directory
    working_dir_status = check_working_directory()

    # Find sensitive files
    sensitive_files = find_sensitive_files()

    # Build result
    issues_count = invalid_commits + (0 if branch_validation["valid"] else 1) + len(sensitive_files)
    can_proceed = issues_count == 0

    result = {
        "status": "success" if can_proceed else "warning",
        "git": {
            "commits": {
                "valid": valid_commits,
                "invalid": invalid_commits,
                "issues": commit_issues[:5]  # Limit to 5
            },
            "branch": {
                "name": branch_name,
                **branch_validation
            },
            "hygiene": {
                "workingDirectory": working_dir_status,
                "untrackedSensitive": sensitive_files
            }
        },
        "canProceed": can_proceed
    }

    if not can_proceed:
        details = []
        if invalid_commits > 0:
            details.append(f"{invalid_commits} commit message issue(s)")
        if not branch_validation["valid"]:
            details.append("invalid branch name")
        if sensitive_files:
            details.append(f"{len(sensitive_files)} sensitive file(s)")

        result["details"] = " and ".join(details) + " found"

    return result


def main():
    """Main entry point"""
    try:
        result = validate_git_hygiene()
        print(json.dumps(result, indent=2))

        # Print summary
        if result.get("status") == "success":
            print("✅ Git hygiene validation passed", file=sys.stderr)
        elif result.get("status") == "warning":
            print(f"⚠️  Git hygiene issues: {result.get('details')}", file=sys.stderr)
        else:
            print(f"❌ Git hygiene validation failed: {result.get('error')}", file=sys.stderr)

        sys.exit(0 if result.get("canProceed", False) else 1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to validate git hygiene"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
