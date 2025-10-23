#!/usr/bin/env python3
"""
Quality Gate API Skill

Runs comprehensive quality checks for TypeScript/JavaScript projects and returns structured results.
This skill is executed in Claude's secure code execution environment.

Works with any project using standard tooling: npm, tsc, Vitest/Jest.
"""

import subprocess
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def run_command(cmd: List[str], cwd: str = None) -> Dict[str, Any]:
    """Run shell command and capture output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timeout after 5 minutes",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "exit_code": -1
        }


def check_typescript(project_path: str) -> Dict[str, Any]:
    """Validate TypeScript compilation."""
    print("🔍 Checking TypeScript...")

    result = run_command(
        ["npx", "tsc", "--noEmit", "--pretty", "false"],
        cwd=project_path
    )

    errors = []
    if not result["success"] and result["stderr"]:
        # Parse TypeScript errors
        error_pattern = r'(.+\.tsx?)\((\d+),(\d+)\): error (TS\d+): (.+)'
        for match in re.finditer(error_pattern, result["stderr"]):
            errors.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "code": match.group(4),
                "message": match.group(5)
            })

    return {
        "passed": result["success"],
        "error_count": len(errors),
        "errors": errors[:10],  # Limit to first 10 errors
        "raw_output": result["stderr"] if not result["success"] else ""
    }


def run_tests(project_path: str) -> Dict[str, Any]:
    """Run test suite."""
    print("🧪 Running tests...")

    # Check if tests are configured
    package_json = Path(project_path) / "package.json"
    if not package_json.exists():
        return {
            "passed": False,
            "error": "package.json not found",
            "skipped": True
        }

    with open(package_json) as f:
        pkg = json.load(f)

    if "test" not in pkg.get("scripts", {}):
        return {
            "passed": True,
            "warning": "No test script configured",
            "skipped": True
        }

    result = run_command(["npm", "test", "--", "--passWithNoTests"], cwd=project_path)

    # Parse test results
    test_summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }

    # Try to extract test counts from output
    output = result["stdout"] + result["stderr"]

    # Jest format: "Tests: 5 passed, 5 total"
    test_match = re.search(r'Tests:\s+(\d+)\s+passed.*?(\d+)\s+total', output)
    if test_match:
        test_summary["passed"] = int(test_match.group(1))
        test_summary["total"] = int(test_match.group(2))
        test_summary["failed"] = test_summary["total"] - test_summary["passed"]

    return {
        "passed": result["success"],
        "summary": test_summary,
        "output": output[-1000:] if not result["success"] else ""  # Last 1000 chars on failure
    }


def check_coverage(project_path: str, threshold: int = 80) -> Dict[str, Any]:
    """Check test coverage against threshold."""
    print("📊 Checking coverage...")

    # Check if coverage is configured
    package_json = Path(project_path) / "package.json"
    if not package_json.exists():
        return {
            "passed": True,
            "warning": "package.json not found",
            "skipped": True
        }

    with open(package_json) as f:
        pkg = json.load(f)

    if "test:coverage" not in pkg.get("scripts", {}):
        return {
            "passed": True,
            "warning": "No coverage script configured",
            "skipped": True
        }

    result = run_command(["npm", "run", "test:coverage"], cwd=project_path)

    # Parse coverage from output
    coverage_data = {
        "statements": 0,
        "branches": 0,
        "functions": 0,
        "lines": 0
    }

    # Jest coverage format: "Statements   : 85.5% ( 123/144 )"
    for metric in ["statements", "branches", "functions", "lines"]:
        pattern = rf'{metric.capitalize()}\s*:\s*([\d.]+)%'
        match = re.search(pattern, result["stdout"], re.IGNORECASE)
        if match:
            coverage_data[metric] = float(match.group(1))

    avg_coverage = sum(coverage_data.values()) / len(coverage_data) if coverage_data else 0

    return {
        "passed": avg_coverage >= threshold,
        "coverage": coverage_data,
        "average": round(avg_coverage, 2),
        "threshold": threshold,
        "output": result["stdout"][-500:] if not result["success"] else ""
    }


def run_build(project_path: str) -> Dict[str, Any]:
    """Try building the project."""
    print("🏗️  Running build...")

    result = run_command(["npm", "run", "build"], cwd=project_path)

    return {
        "passed": result["success"],
        "output": result["stderr"][-500:] if not result["success"] else ""
    }


def run_lint(project_path: str) -> Dict[str, Any]:
    """Run linter."""
    print("🧹 Running linter...")

    # Check if lint script exists
    package_json = Path(project_path) / "package.json"
    if not package_json.exists():
        return {
            "passed": True,
            "warning": "package.json not found",
            "skipped": True
        }

    with open(package_json) as f:
        pkg = json.load(f)

    if "lint" not in pkg.get("scripts", {}):
        return {
            "passed": True,
            "warning": "No lint script configured",
            "skipped": True
        }

    result = run_command(["npm", "run", "lint"], cwd=project_path)

    return {
        "passed": result["success"],
        "output": result["stdout"][-500:] if not result["success"] else ""
    }


def quality_gate(project_path: str = ".", coverage_threshold: int = 80) -> Dict[str, Any]:
    """
    Run comprehensive quality gate checks.

    Args:
        project_path: Path to project directory (default: current directory)
        coverage_threshold: Minimum coverage percentage (default: 80)

    Returns:
        Dictionary with results of all quality checks
    """
    print(f"🚦 Running Quality Gate for: {project_path}")
    print(f"Coverage threshold: {coverage_threshold}%\n")

    # Resolve absolute path
    project_path = os.path.abspath(project_path)

    if not os.path.exists(project_path):
        return {
            "passed": False,
            "error": f"Project path not found: {project_path}"
        }

    # Run all checks
    results = {
        "typescript": check_typescript(project_path),
        "tests": run_tests(project_path),
        "coverage": check_coverage(project_path, coverage_threshold),
        "build": run_build(project_path),
        "lint": run_lint(project_path)
    }

    # Determine overall pass/fail
    all_passed = all(
        r.get("passed", False) or r.get("skipped", False)
        for r in results.values()
    )

    # Count results
    checks_run = sum(1 for r in results.values() if not r.get("skipped", False))
    checks_passed = sum(1 for r in results.values() if r.get("passed", False))
    checks_failed = sum(1 for r in results.values() if not r.get("passed", False) and not r.get("skipped", False))

    # Generate summary
    summary = {
        "passed": all_passed,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "details": results
    }

    # Print summary
    print("\n" + "="*50)
    print("📋 Quality Gate Summary:")
    print("="*50)

    for check_name, check_result in results.items():
        status = "✅" if check_result.get("passed") else "⏭️" if check_result.get("skipped") else "❌"
        print(f"{status} {check_name.upper()}")

        if check_result.get("error_count"):
            print(f"   Errors: {check_result['error_count']}")
        if check_result.get("summary"):
            print(f"   Tests: {check_result['summary']}")
        if check_result.get("average"):
            print(f"   Coverage: {check_result['average']}%")

    print("="*50)
    print(f"{'✅ PASSED' if all_passed else '❌ FAILED'}: {checks_passed}/{checks_run} checks passed")
    print("="*50)

    return summary


# Entry point for Claude Code Execution
if __name__ == "__main__":
    import sys

    # Parse command line arguments
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    coverage_threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 80

    # Run quality gate
    result = quality_gate(project_path, coverage_threshold)

    # Output JSON result
    print("\n📤 Result JSON:")
    print(json.dumps(result, indent=2))
