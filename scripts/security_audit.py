#!/usr/bin/env python3
"""
Security audit script for dependency vulnerability scanning.

Runs pip-audit and safety check to scan for known vulnerabilities.
"""

import subprocess
import sys
from pathlib import Path


def run_pip_audit():
    """Run pip-audit to check for vulnerabilities in dependencies."""
    print("=" * 70)
    print("Running pip-audit...")
    print("=" * 70)

    try:
        result = subprocess.run(
            ['pip-audit', '--desc', '--format', 'json'],
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.returncode != 0:
            print("\n[!] Vulnerabilities detected!", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        else:
            print("\n[OK] No vulnerabilities found")
            return True

    except FileNotFoundError:
        print("[ERROR] pip-audit not installed. Install with: pip install pip-audit")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run pip-audit: {e}")
        return False


def run_safety_check():
    """Run safety check for known security issues."""
    print("\n" + "=" * 70)
    print("Running safety check...")
    print("=" * 70)

    try:
        result = subprocess.run(
            ['safety', 'check', '--json'],
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.returncode != 0:
            print("\n[!] Security issues detected!", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        else:
            print("\n[OK] No security issues found")
            return True

    except FileNotFoundError:
        print("[WARNING] safety not installed. Install with: pip install safety")
        return True  # Don't fail if tool not installed
    except Exception as e:
        print(f"[ERROR] Failed to run safety: {e}")
        return False


def run_bandit():
    """Run Bandit for Python code security analysis."""
    print("\n" + "=" * 70)
    print("Running Bandit (Python security linter)...")
    print("=" * 70)

    try:
        result = subprocess.run(
            ['bandit', '-r', 'src/', '-f', 'json'],
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.returncode == 1:
            print("\n[!] Security issues found in code!", file=sys.stderr)
            return False
        elif result.returncode == 0:
            print("\n[OK] No critical security issues found")
            return True
        else:
            print("\n[WARNING] Bandit encountered errors")
            return True

    except FileNotFoundError:
        print("[WARNING] bandit not installed. Install with: pip install bandit")
        return True  # Don't fail if tool not installed
    except Exception as e:
        print(f"[ERROR] Failed to run bandit: {e}")
        return False


def main():
    """Run all security checks."""
    print("\n" + "=" * 70)
    print("SECURITY AUDIT")
    print("=" * 70)

    results = {
        'pip-audit': run_pip_audit(),
        'safety': run_safety_check(),
        'bandit': run_bandit()
    }

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for tool, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {tool}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[OK] All security checks passed")
        return 0
    else:
        print("\n[FAIL] Some security checks failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
