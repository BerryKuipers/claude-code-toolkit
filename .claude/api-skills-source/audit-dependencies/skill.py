#!/usr/bin/env python3
"""
Audit Dependencies - Run npm audit and outdated checks
"""

import subprocess
import json
import sys
from pathlib import Path


def run_npm_audit():
    """Run npm audit and parse results"""
    if not Path('package.json').exists():
        return {
            "status": "error",
            "error": "package.json not found",
            "details": "Not in a Node.js project directory"
        }

    print("→ Running npm audit...", file=sys.stderr)

    # Run npm audit with JSON output
    result = subprocess.run(
        ['npm', 'audit', '--json'],
        capture_output=True,
        text=True
    )

    try:
        audit_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # npm audit might fail to parse, try basic parsing
        return parse_audit_text(result.stdout + result.stderr)

    # Extract vulnerability counts
    vulnerabilities = audit_data.get('metadata', {}).get('vulnerabilities', {})

    vuln_summary = {
        "critical": vulnerabilities.get('critical', 0),
        "high": vulnerabilities.get('high', 0),
        "moderate": vulnerabilities.get('moderate', 0),
        "low": vulnerabilities.get('low', 0),
        "total": vulnerabilities.get('total', 0)
    }

    # Extract affected packages
    packages = []
    advisories = audit_data.get('advisories', {})

    for advisory_id, advisory in list(advisories.items())[:10]:  # Limit to 10
        packages.append({
            "name": advisory.get('module_name'),
            "severity": advisory.get('severity'),
            "via": [advisory.get('title')] if advisory.get('title') else [],
            "fix": f"npm update {advisory.get('module_name')}"
        })

    return vuln_summary, packages


def run_npm_outdated():
    """Check for outdated packages"""
    print("→ Checking for outdated packages...", file=sys.stderr)

    result = subprocess.run(
        ['npm', 'outdated', '--json'],
        capture_output=True,
        text=True
    )

    try:
        outdated_data = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {"count": 0, "packages": []}

    packages = []
    for pkg_name, pkg_info in list(outdated_data.items())[:15]:  # Limit to 15
        current = pkg_info.get('current', 'unknown')
        latest = pkg_info.get('latest', 'unknown')

        # Determine update type (patch/minor/major)
        update_type = determine_update_type(current, latest)

        packages.append({
            "name": pkg_name,
            "current": current,
            "latest": latest,
            "type": update_type
        })

    return {
        "count": len(outdated_data),
        "packages": packages
    }


def determine_update_type(current, latest):
    """Determine if update is patch, minor, or major"""
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]

        if current_parts[0] != latest_parts[0]:
            return "major"
        elif len(current_parts) > 1 and len(latest_parts) > 1 and current_parts[1] != latest_parts[1]:
            return "minor"
        else:
            return "patch"
    except:
        return "unknown"


def parse_audit_text(output):
    """Fallback text parsing for npm audit"""
    import re

    # Look for summary line
    # "found 20 vulnerabilities (3 low, 10 moderate, 5 high, 2 critical)"
    pattern = r'found (\d+) vulnerabilit(?:y|ies)\s+\((?:(\d+) low)?[,\s]*(?:(\d+) moderate)?[,\s]*(?:(\d+) high)?[,\s]*(?:(\d+) critical)?\)'

    match = re.search(pattern, output)

    if match:
        return {
            "critical": int(match.group(5)) if match.group(5) else 0,
            "high": int(match.group(4)) if match.group(4) else 0,
            "moderate": int(match.group(3)) if match.group(3) else 0,
            "low": int(match.group(2)) if match.group(2) else 0,
            "total": int(match.group(1))
        }, []

    return {
        "critical": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "total": 0
    }, []


def main():
    """Main entry point"""
    try:
        # Run audit
        vuln_result = run_npm_audit()

        if isinstance(vuln_result, dict) and vuln_result.get("status") == "error":
            print(json.dumps(vuln_result, indent=2))
            sys.exit(1)

        vuln_summary, packages = vuln_result

        # Run outdated check
        outdated = run_npm_outdated()

        # Determine status
        critical = vuln_summary.get("critical", 0)
        high = vuln_summary.get("high", 0)
        total = vuln_summary.get("total", 0)

        can_proceed = (critical == 0 and high == 0)
        status = "success" if can_proceed else "error"

        result = {
            "status": status,
            "audit": {
                "vulnerabilities": vuln_summary,
                "packages": packages,
                "outdated": outdated
            },
            "canProceed": can_proceed
        }

        if not can_proceed:
            result["details"] = f"{critical} critical and {high} high severity vulnerabilities must be fixed"

        print(json.dumps(result, indent=2))

        # Print summary to stderr
        if total > 0:
            print(f"❌ Found {total} vulnerabilities ({critical} critical, {high} high)", file=sys.stderr)
        else:
            print(f"✅ No vulnerabilities found", file=sys.stderr)

        if outdated["count"] > 0:
            print(f"ℹ️  {outdated['count']} packages are outdated", file=sys.stderr)

        sys.exit(0 if can_proceed else 1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to run dependency audit"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
