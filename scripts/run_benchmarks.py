#!/usr/bin/env python3
"""
Benchmark runner script.

Runs all performance benchmarks and generates a summary report.
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import argparse


def get_hardware_info():
    """Get current hardware information."""
    import platform
    import psutil

    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    except ImportError:
        gpu_available = False
        gpu_name = None

    return {
        'cpu': {
            'platform': platform.machine(),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
        },
        'ram': {
            'total_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        },
        'gpu': {
            'available': gpu_available,
            'name': gpu_name if gpu_available else None,
        },
        'platform': platform.system(),
    }


def run_benchmark_tests(
    smoke_only: bool = False,
    verbose: bool = False
) -> subprocess.CompletedProcess:
    """
    Run pytest on performance tests.

    Args:
        smoke_only: Only run smoke tests
        verbose: Enable verbose output

    Returns:
        Subprocess result
    """
    pytest_args = [
        'pytest',
        'tests/performance/',
        '-v' if verbose else '',
        '--tb=short',
        '--strict-markers',
    ]

    if smoke_only:
        pytest_args.extend(['-m', 'smoke'])
    else:
        pytest_args.extend(['-m', 'benchmark'])

    # Filter out empty strings
    pytest_args = [arg for arg in pytest_args if arg]

    print(f"Running: {' '.join(pytest_args)}\n")

    result = subprocess.run(
        pytest_args,
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )

    return result


def generate_report(
    result: subprocess.CompletedProcess,
    hardware: dict,
    output_file: str = None
) -> dict:
    """
    Generate benchmark report from test results.

    Args:
        result: Pytest subprocess result
        hardware: Hardware information
        output_file: Optional output file path

    Returns:
        Report dictionary
    """
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'hardware': hardware,
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'success': result.returncode == 0,
    }

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Report saved to: {output_file}")

    return report


def print_summary(report: dict):
    """Print benchmark summary."""
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

    print(f"\nTimestamp: {report['timestamp']}")

    hw = report['hardware']
    print(f"\nHardware:")
    print(f"  CPU: {hw['cpu']['cores']} cores, {hw['cpu']['threads']} threads")
    print(f"  RAM: {hw['ram']['total_gb']}GB")
    if hw['gpu']['available']:
        print(f"  GPU: {hw['gpu']['name']}")
    else:
        print(f"  GPU: Not available")

    print(f"\nStatus: {'✅ PASSED' if report['success'] else '❌ FAILED'}")
    print(f"Exit Code: {report['exit_code']}")

    if not report['success']:
        print(f"\n❌ Benchmarks failed!")
        if report['stderr']:
            print(f"\nErrors:\n{report['stderr']}")


def main():
    parser = argparse.ArgumentParser(
        description="Run performance benchmarks and generate report"
    )
    parser.add_argument(
        '--smoke',
        action='store_true',
        help='Run only smoke tests (quick check)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output JSON file path (default: benchmark_results.json)'
    )
    parser.add_argument(
        '--check-regression',
        action='store_true',
        help='Check results against baseline for regression'
    )

    args = parser.parse_args()

    print("="*60)
    print("PERFORMANCE BENCHMARK SUITE")
    print("="*60)

    # Get hardware info
    hardware = get_hardware_info()
    print(f"\nHardware: {hardware['cpu']['cores']} cores, {hardware['ram']['total_gb']}GB RAM")

    # Run benchmarks
    test_type = "Smoke" if args.smoke else "Full"
    print(f"\nRunning {test_type} benchmarks...")
    result = run_benchmark_tests(smoke_only=args.smoke, verbose=args.verbose)

    # Generate report
    output_file = args.output or f"benchmark_results_{'smoke' if args.smoke else 'full'}.json"
    report = generate_report(result, hardware, output_file)

    # Print summary
    print_summary(report)

    # Check regression if requested
    if args.check_regression and report['success']:
        print("\nChecking for regression...")
        regression_check = subprocess.run(
            [sys.executable, 'scripts/check_regression.py', output_file],
            capture_output=True,
            text=True
        )
        print(regression_check.stdout)

    # Exit with appropriate code
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
