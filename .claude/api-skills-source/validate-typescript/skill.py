#!/usr/bin/env python3
"""
Validate TypeScript - Run tsc --noEmit and return structured results
"""

import subprocess
import re
import json
import sys
import os
from pathlib import Path


def find_tsc_command():
    """Find available TypeScript compiler command"""
    # Try tsc in PATH
    if subprocess.run(['which', 'tsc'], capture_output=True).returncode == 0:
        return ['tsc']

    # Try npx tsc
    if subprocess.run(['which', 'npx'], capture_output=True).returncode == 0:
        return ['npx', 'tsc']

    return None


def run_typescript_check():
    """Run TypeScript type checking"""
    tsc_cmd = find_tsc_command()

    if not tsc_cmd:
        return {
            "status": "error",
            "error": "TypeScript not available",
            "suggestion": "Install TypeScript: npm install --save-dev typescript"
        }

    # Check for tsconfig.json
    if not Path('tsconfig.json').exists():
        print("⚠️ Warning: tsconfig.json not found - using default config", file=sys.stderr)

    # Run tsc --noEmit
    print(f"→ Running TypeScript type check with: {' '.join(tsc_cmd)}", file=sys.stderr)

    result = subprocess.run(
        tsc_cmd + ['--noEmit'],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    # Parse results
    if result.returncode == 0:
        print("✅ TypeScript validation passed", file=sys.stderr)
        return {
            "status": "success",
            "typescript": {
                "status": "passing",
                "errors": {
                    "total": 0,
                    "type": 0,
                    "syntax": 0,
                    "import": 0
                },
                "files": []
            },
            "canProceed": True
        }
    else:
        print("❌ TypeScript validation failed", file=sys.stderr)
        return parse_typescript_errors(output)


def parse_typescript_errors(output):
    """Parse TypeScript error output"""
    # Find all error lines
    error_pattern = r'error TS(\d+):'
    errors = re.findall(error_pattern, output)

    total_errors = len(errors)

    # Categorize errors
    type_errors = len([e for e in errors if e.startswith('2') and e != '2307'])
    syntax_errors = len([e for e in errors if e.startswith('1')])
    import_errors = len([e for e in errors if e == '2307'])

    # Extract files with errors
    file_pattern = r'^(.+\.tsx?)\(\d+,\d+\):'
    file_matches = re.findall(file_pattern, output, re.MULTILINE)
    error_files = sorted(set(file_matches))

    print(f"   Errors: {total_errors}", file=sys.stderr)
    print(f"   Type errors: {type_errors}", file=sys.stderr)
    print(f"   Syntax errors: {syntax_errors}", file=sys.stderr)
    print(f"   Import errors: {import_errors}", file=sys.stderr)

    return {
        "status": "error",
        "typescript": {
            "status": "failing",
            "errors": {
                "total": total_errors,
                "type": type_errors,
                "syntax": syntax_errors,
                "import": import_errors
            },
            "files": error_files
        },
        "canProceed": False,
        "details": f"{total_errors} TypeScript error{'s' if total_errors != 1 else ''} must be fixed before proceeding"
    }


def main():
    """Main entry point"""
    try:
        result = run_typescript_check()
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get("status") == "success" else 1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to run TypeScript validation"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
