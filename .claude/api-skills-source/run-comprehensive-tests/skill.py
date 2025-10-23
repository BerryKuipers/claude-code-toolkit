#!/usr/bin/env python3
"""
Run Comprehensive Tests - Execute test suite and return structured results
"""

import subprocess
import re
import json
import sys
from pathlib import Path


def run_tests():
    """Run test suite with coverage"""
    # Check if package.json exists
    if not Path('package.json').exists():
        return {
            "status": "error",
            "error": "package.json not found",
            "details": "Not in a Node.js project directory"
        }

    # Check if node_modules exists
    if not Path('node_modules').exists():
        return {
            "status": "error",
            "error": "node_modules not found",
            "details": "Run npm install first"
        }

    print("→ Running comprehensive test suite...", file=sys.stderr)

    # Run tests
    result = subprocess.run(
        ['npm', 'run', 'test'],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    output = result.stdout + result.stderr

    # Parse test results
    return parse_test_results(output, result.returncode)


def parse_test_results(output, exit_code):
    """Parse test output for results"""
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "coverage": 0.0,
        "duration": "0s"
    }
    failures = []

    # Parse Vitest output
    # Look for patterns like:
    # "Test Files  1 passed (1)"
    # "Tests  45 passed (45)"
    # "Test Files  2 passed | 1 failed (3 total)"

    # Extract test counts
    test_pattern = r'Tests?\s+(\d+)\s+passed(?:\s+\|\s+(\d+)\s+failed)?\s+\((\d+)'
    test_match = re.search(test_pattern, output)

    if test_match:
        passed = int(test_match.group(1))
        failed = int(test_match.group(2)) if test_match.group(2) else 0
        total = int(test_match.group(3))

        summary["passed"] = passed
        summary["failed"] = failed
        summary["total"] = total

    # Extract coverage
    coverage_pattern = r'All files\s+\|\s+(\d+\.?\d*)'
    coverage_match = re.search(coverage_pattern, output)
    if coverage_match:
        summary["coverage"] = float(coverage_match.group(1))

    # Extract duration
    duration_pattern = r'Duration\s+(\d+\.?\d*\w+)'
    duration_match = re.search(duration_pattern, output)
    if duration_match:
        summary["duration"] = duration_match.group(1)

    # Parse failures if any
    if summary["failed"] > 0:
        failures = parse_failures(output)

    # Determine status
    if exit_code == 0 and summary["failed"] == 0:
        status = "pass"
        can_proceed = True
        print(f"✅ All tests passed ({summary['passed']}/{summary['total']})", file=sys.stderr)
    else:
        status = "fail"
        can_proceed = False
        print(f"❌ Tests failed ({summary['failed']} failed, {summary['passed']} passed)", file=sys.stderr)

    result = {
        "status": status,
        "summary": summary,
        "failures": failures,
        "canProceed": can_proceed
    }

    if not can_proceed:
        result["details"] = f"{summary['failed']} test(s) failed"

    return result


def parse_failures(output):
    """Extract failure details from test output"""
    failures = []

    # Look for failure patterns in Vitest output
    # Pattern: FAIL  src/components/Test.test.tsx > Test Suite > test name
    failure_pattern = r'FAIL\s+([^\s]+)\s+>\s+([^>]+)\s+>\s+(.+)'

    # Error patterns to extract from subsequent lines
    error_patterns = [
        r'AssertionError: (.+)',
        r'Error: (.+)',
        r'Expected (.+)',
        r'Received (.+)',
        r'TypeError: (.+)',
        r'ReferenceError: (.+)'
    ]

    # Line number pattern in stack traces
    line_pattern = r'at .+?:(\d+):\d+'

    lines = output.split('\n')

    for i, line in enumerate(lines):
        match = re.search(failure_pattern, line)
        if match:
            file_path = match.group(1).strip()
            suite = match.group(2).strip()
            test_name = match.group(3).strip()

            # Look ahead in next 10 lines for error details
            error_msg = "Test failed"
            line_number = 0

            for j in range(i + 1, min(i + 11, len(lines))):
                next_line = lines[j]

                # Try to extract error message
                for error_pat in error_patterns:
                    err_match = re.search(error_pat, next_line)
                    if err_match:
                        error_msg = err_match.group(1).strip()
                        break

                # Try to extract line number from stack trace
                line_match = re.search(line_pattern, next_line)
                if line_match:
                    line_number = int(line_match.group(1))

                # Stop if we found both or hit another FAIL
                if (error_msg != "Test failed" and line_number > 0) or 'FAIL' in next_line:
                    break

            failures.append({
                "file": file_path,
                "test": f"{suite} > {test_name}",
                "error": error_msg,
                "line": line_number
            })

    # Limit to first 10 failures for clarity
    return failures[:10]


def main():
    """Main entry point"""
    try:
        result = run_tests()
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get("status") == "pass" else 1)

    except subprocess.TimeoutExpired:
        error_result = {
            "status": "error",
            "error": "Test execution timed out",
            "details": "Tests took longer than 5 minutes"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to run tests"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
