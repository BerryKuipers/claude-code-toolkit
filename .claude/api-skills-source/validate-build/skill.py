#!/usr/bin/env python3
"""
Validate Build - Run production build and return structured results
"""

import subprocess
import re
import json
import sys
import time
from pathlib import Path


def find_build_command():
    """Find available build command"""
    if not Path('package.json').exists():
        return None

    with open('package.json') as f:
        pkg = json.load(f)
        scripts = pkg.get('scripts', {})

        # Check for common build script names
        if 'build' in scripts:
            return ['npm', 'run', 'build']
        if 'build:prod' in scripts:
            return ['npm', 'run', 'build:prod']
        if 'compile' in scripts:
            return ['npm', 'run', 'compile']

    return None


def run_build():
    """Run production build"""
    build_cmd = find_build_command()

    if not build_cmd:
        return {
            "status": "error",
            "error": "No build script found",
            "suggestion": "Add build script to package.json"
        }

    # Check node_modules exists
    if not Path('node_modules').exists():
        return {
            "status": "error",
            "error": "node_modules not found",
            "details": "Run npm install first"
        }

    print(f"→ Running build with: {' '.join(build_cmd)}", file=sys.stderr)

    # Time the build
    start_time = time.time()

    # Run build
    result = subprocess.run(
        build_cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    duration = time.time() - start_time
    duration_str = f"{duration:.1f}s"

    output = result.stdout + result.stderr

    # Parse results
    return parse_build_output(output, result.returncode, duration_str)


def parse_build_output(output, exit_code, duration):
    """Parse build output for errors and warnings"""
    errors = []
    warnings = []
    output_size = None

    # Vite build success pattern
    # "dist/index.html  0.45 kB │ gzip: 0.30 kB"
    # "dist/assets/index-abc123.js  245.8 kB │ gzip: 75.2 kB"

    # Extract output size
    size_pattern = r'(\d+\.?\d*)\s+(kB|MB)'
    size_matches = re.findall(size_pattern, output)
    if size_matches:
        # Get largest file size
        sizes = [(float(m[0]), m[1]) for m in size_matches]
        max_size, unit = max(sizes, key=lambda x: x[0])
        output_size = f"{max_size} {unit}"

    # TypeScript/Vite error pattern
    # "src/components/Settings.tsx(42,10): error TS2339: Property 'user' does not exist"
    error_pattern = r'([^\s]+\.tsx?)\((\d+),\d+\):\s+error\s+\w+:\s+(.+)'

    for match in re.finditer(error_pattern, output):
        errors.append({
            "file": match.group(1),
            "line": int(match.group(2)),
            "message": match.group(3).strip()
        })

    # Warning patterns
    warning_pattern = r'warning:\s+(.+)'
    for match in re.finditer(warning_pattern, output, re.IGNORECASE):
        warnings.append({
            "message": match.group(1).strip()
        })

    # Circular dependency warnings (common in Vite)
    circular_pattern = r'Circular dependency:\s+(.+)'
    for match in re.finditer(circular_pattern, output):
        warnings.append({
            "message": "Circular dependency detected",
            "details": match.group(1).strip()
        })

    # Determine status
    if exit_code == 0:
        print(f"✅ Build passed in {duration}", file=sys.stderr)
        return {
            "status": "success",
            "build": {
                "status": "passing",
                "duration": duration,
                "outputSize": output_size or "unknown",
                "errors": [],
                "warnings": warnings[:10]  # Limit warnings
            },
            "canProceed": True
        }
    else:
        print(f"❌ Build failed in {duration} with {len(errors)} error(s)", file=sys.stderr)

        result = {
            "status": "error",
            "build": {
                "status": "failing",
                "duration": duration,
                "errors": errors[:10],  # Limit to first 10 errors
                "warnings": warnings[:10]
            },
            "canProceed": False,
            "details": f"Build failed with {len(errors) if errors else 'unknown'} error(s)"
        }

        return result


def main():
    """Main entry point"""
    try:
        result = run_build()
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get("status") == "success" else 1)

    except subprocess.TimeoutExpired:
        error_result = {
            "status": "error",
            "error": "Build timed out",
            "details": "Build took longer than 5 minutes"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "details": "Failed to run build"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
