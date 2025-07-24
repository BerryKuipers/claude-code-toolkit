#!/usr/bin/env python3
"""
Test runner for the crypto-insight project.
Runs all tests and provides a summary of results.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests and return results."""
    print("🧪 Running Crypto Insight Test Suite")
    print("=" * 60)

    # Get the tests directory
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent

    # Change to project root for consistent imports
    os.chdir(project_root)

    # Run pytest with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test_category(category):
    """Run tests for a specific category."""
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    os.chdir(project_root)

    test_files = {
        "chat": "test_chat_functionality.py",
        "api": "test_api_keys.py",
        "core": "test_core.py",
        "ai": "test_ai_explanations.py",
        "cli": "test_cli.py",
    }

    if category not in test_files:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(test_files.keys())}")
        return False

    test_file = tests_dir / test_files[category]
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    print(f"🧪 Running {category} tests")
    print("=" * 40)
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {category} tests: {e}")
        return False


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        # Run specific test category
        category = sys.argv[1]
        success = run_specific_test_category(category)
    else:
        # Run all tests
        success = run_tests()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
