#!/usr/bin/env python3
"""
Performance regression detection script.

Checks benchmark results against baseline to detect performance degradation.
Fails if regression exceeds threshold (default 10%).
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


def check_regression(
    current_results: Dict[str, Any],
    baseline: Dict[str, Any],
    threshold: float = 0.10
) -> List[Dict[str, Any]]:
    """
    Check if current performance regressed vs baseline.

    Args:
        current_results: Current benchmark results
        baseline: Baseline benchmark results
        threshold: Regression threshold (e.g., 0.10 = 10%)

    Returns:
        List of regression detected (empty if none)
    """
    regressions = []

    benchmarks = current_results.get('benchmarks', {})
    baseline_benchmarks = baseline.get('benchmarks', {})

    for name, metrics in benchmarks.items():
        if name not in baseline_benchmarks:
            continue

        baseline_metrics = baseline_benchmarks[name]

        # Check latency regression (higher is worse)
        if 'current_ms' in metrics and 'baseline_ms' in baseline_metrics:
            current_val = metrics['current_ms']
            baseline_val = baseline_metrics['baseline_ms']

            if current_val > baseline_val * (1 + threshold):
                regressions.append({
                    'benchmark': name,
                    'metric': 'latency',
                    'baseline': baseline_val,
                    'current': current_val,
                    'degradation': f"{((current_val / baseline_val) - 1) * 100:.1f}%",
                    'threshold': f"{threshold * 100:.0f}%"
                })

        # Check speedup regression (lower is worse)
        if 'speedup' in metrics and 'speedup' in baseline_metrics:
            current_val = metrics['speedup']
            baseline_val = baseline_metrics['speedup']

            if current_val < baseline_val * (1 - threshold):
                regressions.append({
                    'benchmark': name,
                    'metric': 'speedup',
                    'baseline': baseline_val,
                    'current': current_val,
                    'degradation': f"{((baseline_val / current_val) - 1) * 100:.1f}%",
                    'threshold': f"{threshold * 100:.0f}%"
                })

        # Check fps regression (lower is worse)
        if 'fps' in metrics and 'fps' in baseline_metrics:
            current_val = metrics.get('batch_fps', metrics.get('async_fps', metrics.get('fps')))
            baseline_val = baseline_metrics.get('batch_fps', baseline_metrics.get('sync_fps', baseline_metrics.get('fps')))

            if current_val and baseline_val and current_val < baseline_val * (1 - threshold):
                regressions.append({
                    'benchmark': name,
                    'metric': 'throughput',
                    'baseline': baseline_val,
                    'current': current_val,
                    'degradation': f"{((baseline_val / current_val) - 1) * 100:.1f}%",
                    'threshold': f"{threshold * 100:.0f}%"
                })

    return regressions


def format_regression_message(regressions: List[Dict[str, Any]]) -> str:
    """Format regression results as readable message."""
    if not regressions:
        return "✅ No performance regression detected"

    lines = ["❌ Performance regression detected:\n"]

    for reg in regressions:
        lines.append(f"\n{reg['benchmark']}:")
        lines.append(f"  Metric: {reg['metric']}")
        lines.append(f"  Baseline: {reg['baseline']:.2f}")
        lines.append(f"  Current: {reg['current']:.2f}")
        lines.append(f"  Degradation: {reg['degradation']} (threshold: {reg['threshold']})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check performance benchmark results for regression"
    )
    parser.add_argument(
        'results_file',
        type=str,
        help='Path to current benchmark results JSON file'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        default=None,
        help='Path to baseline JSON file (default: baselines/performance_baseline.json)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.10,
        help='Regression threshold (default: 0.10 = 10%%)'
    )
    parser.add_argument(
        '--update-baseline',
        action='store_true',
        help='Update baseline with current results if no regression'
    )

    args = parser.parse_args()

    # Load current results
    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"❌ Error: Results file not found: {args.results_file}")
        sys.exit(1)

    with open(results_path, 'r') as f:
        current_results = json.load(f)

    # Load baseline
    if args.baseline:
        baseline_path = Path(args.baseline)
    else:
        baseline_path = Path(__file__).parent.parent / "baselines" / "performance_baseline.json"

    if not baseline_path.exists():
        print(f"⚠️  Warning: Baseline file not found: {baseline_path}")
        print("Creating new baseline...")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_path, 'w') as f:
            json.dump(current_results, f, indent=2)
        print(f"✅ Created baseline: {baseline_path}")
        sys.exit(0)

    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    # Check for regression
    regressions = check_regression(current_results, baseline, args.threshold)

    # Format and print results
    message = format_regression_message(regressions)
    print(message)

    # Exit with error if regression detected
    if regressions:
        print("\n❌ Performance regression detected!")
        print("Please investigate and fix before merging.")
        sys.exit(1)

    # Optionally update baseline
    if args.update_baseline:
        print(f"\n📝 Updating baseline: {baseline_path}")
        with open(baseline_path, 'w') as f:
            json.dump(current_results, f, indent=2)
        print("✅ Baseline updated")

    sys.exit(0)


if __name__ == '__main__':
    main()
