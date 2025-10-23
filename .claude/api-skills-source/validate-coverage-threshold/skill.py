#!/usr/bin/env python3
"""
Validate Coverage Threshold - Check coverage meets minimum thresholds
"""

import json
import re
import sys
from pathlib import Path


# Default thresholds
DEFAULT_THRESHOLDS = {
    "overall": 80,
    "statements": 80,
    "branches": 75,
    "functions": 80
}


def load_coverage_data():
    """Load coverage data from available sources"""
    # Try JSON coverage report (preferred)
    json_path = Path('coverage/coverage-summary.json')
    if json_path.exists():
        print(f"→ Loading coverage from {json_path}", file=sys.stderr)
        with open(json_path) as f:
            return json.load(f), "json"

    # Try text output fallback
    text_paths = [
        Path('.claude/baseline/test-output.txt'),
        Path('test-output.txt'),
        Path('coverage.txt')
    ]

    for text_path in text_paths:
        if text_path.exists():
            print(f"→ Loading coverage from text: {text_path}", file=sys.stderr)
            with open(text_path) as f:
                return f.read(), "text"

    # No coverage data found
    return None, None


def extract_coverage_metrics(data, source):
    """Extract coverage metrics from data"""
    if source == "json":
        total = data.get("total", {})
        return {
            "overall": total.get("lines", {}).get("pct", 0),
            "statements": total.get("statements", {}).get("pct", 0),
            "branches": total.get("branches", {}).get("pct", 0),
            "functions": total.get("functions", {}).get("pct", 0)
        }

    elif source == "text":
        # Parse text output for coverage percentages
        # Look for patterns like "All files | 87.5 | 85.2 | 84.1 | 89.3"
        coverage_pattern = r'All files\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
        match = re.search(coverage_pattern, data)

        if match:
            return {
                "overall": float(match.group(1)),
                "statements": float(match.group(2)),
                "branches": float(match.group(3)),
                "functions": float(match.group(4))
            }

        # Fallback: try to find at least overall coverage
        simple_pattern = r'All files.*?(\d+\.?\d*)%?'
        match = re.search(simple_pattern, data)
        if match:
            coverage_val = float(match.group(1))
            return {
                "overall": coverage_val,
                "statements": coverage_val,
                "branches": coverage_val,
                "functions": coverage_val
            }

    return None


def validate_thresholds(coverage, thresholds=None):
    """Validate coverage against thresholds"""
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    print("", file=sys.stderr)
    print("Coverage metrics:", file=sys.stderr)
    print(f"  Overall: {coverage['overall']}%", file=sys.stderr)
    print(f"  Statements: {coverage['statements']}%", file=sys.stderr)
    print(f"  Branches: {coverage['branches']}%", file=sys.stderr)
    print(f"  Functions: {coverage['functions']}%", file=sys.stderr)

    print("", file=sys.stderr)
    print("Minimum thresholds:", file=sys.stderr)
    print(f"  Overall: {thresholds['overall']}%", file=sys.stderr)
    print(f"  Statements: {thresholds['statements']}%", file=sys.stderr)
    print(f"  Branches: {thresholds['branches']}%", file=sys.stderr)
    print(f"  Functions: {thresholds['functions']}%", file=sys.stderr)

    print("", file=sys.stderr)
    print("→ Validating coverage thresholds...", file=sys.stderr)

    failures = []
    passed = True

    # Check each metric
    metrics = [
        ("overall", coverage["overall"], thresholds["overall"]),
        ("statements", coverage["statements"], thresholds["statements"]),
        ("branches", coverage["branches"], thresholds["branches"]),
        ("functions", coverage["functions"], thresholds["functions"])
    ]

    for name, actual, threshold in metrics:
        if actual < threshold:
            msg = f"{name}:{actual}%<{threshold}%"
            failures.append(msg)
            passed = False
            print(f"❌ {name.capitalize()} coverage below threshold: {actual}% < {threshold}%", file=sys.stderr)
        else:
            print(f"✅ {name.capitalize()} coverage: {actual}% ≥ {threshold}%", file=sys.stderr)

    return passed, failures


def find_uncovered_files(data, threshold=80):
    """Find files with coverage below threshold"""
    if not data:
        return []

    uncovered = []

    for file_path, metrics in data.items():
        if file_path == "total":
            continue

        line_coverage = metrics.get("lines", {}).get("pct", 0)
        if line_coverage < threshold:
            uncovered.append({
                "file": file_path,
                "coverage": line_coverage
            })

    # Sort by coverage (lowest first)
    uncovered.sort(key=lambda x: x["coverage"])

    # Limit to top 10
    return uncovered[:10]


def validate_coverage_threshold(thresholds=None):
    """Main validation function"""
    # Load coverage data
    data, source = load_coverage_data()

    if not data:
        return {
            "status": "error",
            "error": "Coverage data not found",
            "suggestion": "Run tests with coverage: npm run test -- --coverage"
        }

    # Extract metrics
    coverage = extract_coverage_metrics(data, source)
    if not coverage:
        return {
            "status": "error",
            "error": "Cannot parse coverage data",
            "suggestion": "Verify coverage output format"
        }

    # Use provided thresholds or defaults
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    # Validate against thresholds
    passed, failures = validate_thresholds(coverage, thresholds)

    # Find uncovered files
    uncovered_files = find_uncovered_files(data) if not passed else []

    # Build result
    result = {
        "status": "success" if passed else "warning",
        "coverage": coverage,
        "thresholds": thresholds,
        "passed": passed,
        "failures": failures,
        "canProceed": passed
    }

    if uncovered_files:
        result["uncoveredFiles"] = uncovered_files

    if not passed:
        result["details"] = f"Coverage below threshold: {len(failures)} metric(s) failed"

    return result


def main():
    """Main entry point"""
    try:
        # Parse threshold arguments if provided
        # Format: overall statements branches functions
        thresholds = None
        if len(sys.argv) > 1:
            thresholds = {
                "overall": float(sys.argv[1]) if len(sys.argv) > 1 else 80,
                "statements": float(sys.argv[2]) if len(sys.argv) > 2 else 80,
                "branches": float(sys.argv[3]) if len(sys.argv) > 3 else 75,
                "functions": float(sys.argv[4]) if len(sys.argv) > 4 else 80
            }

        result = validate_coverage_threshold(thresholds)
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        # Note: Coverage validation returns "warning" not "error" for failures
        sys.exit(0 if result.get("passed") else 1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to validate coverage threshold"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
