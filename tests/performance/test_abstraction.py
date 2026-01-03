"""
Abstraction layer performance benchmarks.

Measures the overhead introduced by the AbstractDetector interface
compared to direct YOLOv8 usage.
"""

import pytest
import numpy as np
from pathlib import Path

# Import detection components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from detection.yolov8 import YOLOv8Detector
from models.yolo_detector import YOLODetector as LegacyYOLODetector


@pytest.mark.benchmark
class TestAbstractionOverhead:
    """
    Test abstraction layer overhead (AC: #1).

    Given implementing new model abstraction layer
    When running performance smoke tests
    Then baseline latency is established
    And abstraction overhead is measured
    And overhead <5% (acceptable threshold)
    """

    def test_abstract_detector_baseline_latency(
        self,
        temp_model_path,
        sample_image_640x640,
        measure_latency,
        warmup_iterations,
        benchmark_iterations
    ):
        """
        Measure baseline latency of AbstractDetector (YOLOv8Detector).

        This establishes the baseline for comparison with legacy detector.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        # Setup
        model_path = "yolov8n.pt"  # Assume model is available
        detector = YOLOv8Detector()
        detector.load_model(model_path, device="cpu")

        # Measure latency
        results = measure_latency(
            detector,
            sample_image_640x640,
            iterations=benchmark_iterations,
            warmup=warmup_iterations
        )

        # Assert performance is reasonable
        assert results['mean'] > 0, "Latency should be positive"
        assert results['mean'] < 1000, f"Latency too high: {results['mean']:.2f}ms"

        print(f"\nAbstractDetector Latency:")
        print(f"  Mean: {results['mean']:.2f}ms")
        print(f"  Median: {results['median']:.2f}ms")
        print(f"  Std: {results['std']:.2f}ms")
        print(f"  Min: {results['min']:.2f}ms")
        print(f"  Max: {results['max']:.2f}ms")

    def test_legacy_detector_latency(
        self,
        sample_image_640x640,
        measure_latency,
        warmup_iterations,
        benchmark_iterations
    ):
        """
        Measure legacy YOLODetector latency for comparison.

        This provides the baseline before abstraction refactoring.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        # Setup
        detector = LegacyYOLODetector(model_path="yolov8n.pt")
        detector.load_model()

        # Convert image format if needed
        # Legacy detector might expect different format
        image = sample_image_640x640

        # Measure latency
        # Note: Legacy detector returns list of dicts, not DetectionResult
        latencies = []

        # Warmup
        for _ in range(warmup_iterations):
            _ = detector.detect(image)

        # Measure
        for _ in range(benchmark_iterations):
            import time
            start = time.perf_counter()
            _ = detector.detect(image)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        results = {
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'std': np.std(latencies),
            'min': np.min(latencies),
            'max': np.max(latencies),
        }

        print(f"\nLegacy Detector Latency:")
        print(f"  Mean: {results['mean']:.2f}ms")
        print(f"  Median: {results['median']:.2f}ms")
        print(f"  Std: {results['std']:.2f}ms")

    def test_abstraction_overhead_threshold(
        self,
        temp_model_path,
        sample_image_640x640,
        measure_latency,
        performance_thresholds,
        save_baseline,
        baseline_path
    ):
        """
        Compare AbstractDetector vs Legacy and verify overhead < 5%.

        This is the main test for AC #1.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        # Setup both detectors
        model_path = "yolov8n.pt"

        abstract_detector = YOLOv8Detector()
        abstract_detector.load_model(model_path, device="cpu")

        legacy_detector = LegacyYOLODetector(model_path=model_path)
        legacy_detector.load_model()

        # Measure both
        abstract_results = measure_latency(abstract_detector, sample_image_640x640)
        legacy_results = measure_latency(legacy_detector, sample_image_640x640)

        # Calculate overhead
        overhead_percent = (
            (abstract_results['mean'] - legacy_results['mean']) /
            legacy_results['mean'] * 100
        )

        # Check threshold
        threshold = performance_thresholds['abstraction_overhead'] * 100  # Convert to percent

        print(f"\nAbstraction Overhead Analysis:")
        print(f"  Legacy: {legacy_results['mean']:.2f}ms")
        print(f"  Abstract: {abstract_results['mean']:.2f}ms")
        print(f"  Overhead: {overhead_percent:.2f}%")
        print(f"  Threshold: {threshold:.1f}%")

        # Update baseline
        import json
        if baseline_path.exists():
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
        else:
            baseline = {"benchmarks": {}}

        baseline['benchmarks']['abstraction_overhead'] = {
            'baseline_ms': legacy_results['mean'],
            'current_ms': abstract_results['mean'],
            'overhead_percent': overhead_percent,
            'status': 'PASS' if overhead_percent < threshold else 'FAIL',
            'threshold': f"{threshold}%"
        }

        save_baseline(baseline_path, baseline)

        # Assert
        assert overhead_percent < threshold, (
            f"Abstraction overhead {overhead_percent:.2f}% exceeds threshold {threshold}%\n"
            f"Legacy: {legacy_results['mean']:.2f}ms, "
            f"Abstract: {abstract_results['mean']:.2f}ms"
        )

    @pytest.mark.smoke
    def test_smoke_abstraction_performance(
        self,
        temp_model_path,
        sample_image_640x640,
        measure_latency,
        performance_thresholds
    ):
        """
        Quick smoke test for abstraction performance.

        Runs minimal iterations to catch major regressions quickly.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Quick measurement
        results = measure_latency(detector, sample_image_640x640, iterations=3, warmup=1)

        # Quick sanity check
        assert results['mean'] < 100, f"Smoke test failed: {results['mean']:.2f}ms too high"
        print(f"\n✅ Smoke test passed: {results['mean']:.2f}ms")


@pytest.mark.benchmark
class TestMemoryOverhead:
    """
    Test memory overhead of abstraction layer.
    """

    def test_memory_usage_comparison(
        self,
        temp_model_path,
        sample_image_640x640,
        measure_memory
    ):
        """
        Compare memory usage between AbstractDetector and Legacy.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        # Setup
        model_path = "yolov8n.pt"

        abstract_detector = YOLOv8Detector()
        abstract_detector.load_model(model_path, device="cpu")

        legacy_detector = LegacyYOLODetector(model_path=model_path)
        legacy_detector.load_model()

        # Measure memory
        abstract_mem = measure_memory(abstract_detector, sample_image_640x640)
        legacy_mem = measure_memory(legacy_detector, sample_image_640x640)

        overhead_mb = abstract_mem['used_mb'] - legacy_mem['used_mb']
        overhead_percent = (overhead_mb / legacy_mem['used_mb']) * 100 if legacy_mem['used_mb'] > 0 else 0

        print(f"\nMemory Overhead:")
        print(f"  Legacy: {legacy_mem['used_mb']:.2f}MB")
        print(f"  Abstract: {abstract_mem['used_mb']:.2f}MB")
        print(f"  Overhead: {overhead_mb:.2f}MB ({overhead_percent:.1f}%)")

        # Memory overhead should be reasonable
        assert overhead_percent < 20, f"Memory overhead {overhead_percent:.1f}% too high"
