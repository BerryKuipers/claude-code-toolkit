#!/usr/bin/env python3
"""
Validate Lint - Run ESLint/Prettier and return structured results
"""

import subprocess
import re
import json
import sys
from pathlib import Path


def find_lint_command():
    """Find available linting command"""
    # Check for npm script first (most common)
    if Path('package.json').exists():
        with open('package.json') as f:
            pkg = json.load(f)
            scripts = pkg.get('scripts', {})

            # Check for common lint script names
            if 'lint' in scripts:
                return ['npm', 'run', 'lint']
            if 'eslint' in scripts:
                return ['npm', 'run', 'eslint']

    # Try eslint directly
    if subprocess.run(['which', 'eslint'], capture_output=True).returncode == 0:
        return ['eslint', '.', '--ext', '.js,.jsx,.ts,.tsx']

    # Try npx eslint
    if subprocess.run(['which', 'npx'], capture_output=True).returncode == 0:
        return ['npx', 'eslint', '.', '--ext', '.js,.jsx,.ts,.tsx']

    return None


def run_lint_check():
    """Run linting validation"""
    lint_cmd = find_lint_command()

    if not lint_cmd:
        return {
            "status": "error",
            "error": "No linting tool available",
            "suggestion": "Install ESLint: npm install --save-dev eslint"
        }

    print(f"→ Running linting with: {' '.join(lint_cmd)}", file=sys.stderr)

    # Run linting
    result = subprocess.run(
        lint_cmd,
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    # Parse results
    return parse_lint_output(output, result.returncode)


def parse_lint_output(output, exit_code):
    """Parse ESLint output for errors and warnings"""
    errors = 0
    warnings = 0
    files = set()
    rule_counts = {}

    # ESLint patterns
    # Format: /path/to/file.ts
    #   1:1  error  'React' is defined but never used  @typescript-eslint/no-unused-vars

    # Count errors and warnings
    error_pattern = r'(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+([\w/-]+)$'

    for line in output.split('\n'):
        match = re.search(error_pattern, line)
        if match:
            severity = match.group(3)
            message = match.group(4)
            rule = match.group(5) if len(match.groups()) >= 5 else 'unknown'

            if severity == 'error':
                errors += 1
            elif severity == 'warning':
                warnings += 1

            # Track rule violations
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

        # Extract file paths
        file_pattern = r'^([^\s]+\.(js|jsx|ts|tsx))$'
        file_match = re.match(file_pattern, line.strip())
        if file_match:
            files.add(file_match.group(1))

    # Alternative: Look for summary line
    # "✖ 17 problems (5 errors, 12 warnings)"
    summary_pattern = r'(\d+)\s+problems?\s+\((\d+)\s+errors?,\s+(\d+)\s+warnings?\)'
    summary_match = re.search(summary_pattern, output)

    if summary_match:
        errors = int(summary_match.group(2))
        warnings = int(summary_match.group(3))

    # Determine status
    if exit_code == 0 and errors == 0:
        print("✅ Linting passed", file=sys.stderr)
        return {
            "status": "success",
            "lint": {
                "status": "passing",
                "errors": 0,
                "warnings": warnings,
                "files": []
            },
            "canProceed": True
        }
    else:
        print(f"❌ Linting failed: {errors} errors, {warnings} warnings", file=sys.stderr)

        # Sort rules by count (most common first)
        sorted_rules = dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True))

        status = "warning" if errors == 0 else "error"
        can_proceed = errors == 0  # Can proceed with warnings, not with errors

        result = {
            "status": status,
            "lint": {
                "status": "failing" if errors > 0 else "warnings",
                "errors": errors,
                "warnings": warnings,
                "files": sorted(list(files))[:20],  # Limit to 20 files
                "rules": sorted_rules
            },
            "canProceed": can_proceed
        }

        if errors > 0:
            result["details"] = f"{errors} linting error(s) must be fixed before proceeding"
        else:
            result["details"] = f"{warnings} linting warning(s) found"

        return result


def main():
    """Main entry point"""
    try:
        result = run_lint_check()
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        # Exit 0 if no errors (warnings OK), exit 1 if errors
        sys.exit(0 if result.get("status") != "error" and result.get("lint", {}).get("errors", 1) == 0 else 1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to run linting validation"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
