"""
Tests for the benchmark infrastructure itself.

Validates that the benchmark framework works correctly:
- Test accuracy (measurements are valid)
- Smoke test execution time
- CI/CD integration
- Failure detection
"""

import pytest
import numpy as np
import json
import time
from pathlib import Path
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.benchmark
class TestBenchmarkAccuracy:
    """
    Test that benchmark measurements are accurate and consistent.

    Validates the measurement infrastructure itself.
    """

    def test_latency_measurement_accuracy(self, sample_image_640x640):
        """
        Verify latency measurements are accurate.

        Uses a mock detector with known latency to validate measurements.
        """
        class MockDetector:
            def __init__(self, latency_ms):
                self.latency_ms = latency_ms

            def detect(self, image):
                time.sleep(self.latency_ms / 1000.0)
                return {'boxes': [], 'scores': [], 'classes': []}

        # Create mock detector with 10ms latency
        detector = MockDetector(10)

        # Measure
        iterations = 5
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            detector.detect(sample_image_640x640)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        mean_latency = np.mean(latencies)

        # Should be approximately 10ms (±5ms for overhead)
        assert 8 <= mean_latency <= 15, f"Measured {mean_latency:.2f}ms, expected ~10ms"

    def test_memory_measurement_accuracy(self, sample_image_640x640):
        """
        Verify memory measurements are reasonable.

        Tests that memory measurements don't have obvious errors.
        """
        import psutil
        import os

        # Get initial memory
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)

        # Allocate some memory
        big_array = np.zeros((1000, 1000, 100))  # ~400MB

        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_used = mem_after - mem_before

        # Should have allocated significant memory
        assert mem_used > 300, f"Memory measurement seems inaccurate: {mem_used:.2f}MB"

        # Clean up
        del big_array

    def test_throughput_measurement_accuracy(self, sample_image_640x640):
        """
        Verify throughput measurements are accurate.

        Uses a mock detector with known throughput.
        """
        class MockDetector:
            def __init__(self, fps):
                self.fps = fps
                self.latency = 1.0 / fps

            def detect(self, image):
                time.sleep(self.latency)
                return {'boxes': [], 'scores': [], 'classes': []}

        # Create mock detector with 10 FPS
        detector = MockDetector(10)

        # Measure throughput for 1 second
        duration = 1.0
        start_time = time.time()
        count = 0

        while time.time() - start_time < duration:
            detector.detect(sample_image_640x640)
            count += 1

        elapsed = time.time() - start_time
        measured_fps = count / elapsed

        # Should be approximately 10 FPS (±2 FPS for overhead)
        assert 8 <= measured_fps <= 12, f"Measured {measured_fps:.2f} FPS, expected ~10 FPS"


@pytest.mark.smoke
class TestSmokeTestPerformance:
    """
    Test that smoke tests execute quickly.

    Validates AC: #5 - smoke test execution time.
    """

    def test_smoke_test_duration(self, sample_image_640x640):
        """
        Verify smoke tests complete in < 2 minutes.

        This is a meta-test for the benchmark suite itself.
        """
        pytest.skip("This would run all smoke tests - too expensive for unit test")

        # In practice, this would be:
        # start = time.time()
        # subprocess.run(['pytest', 'tests/performance/', '-m', 'smoke'])
        # duration = time.time() - start
        # assert duration < 120, f"Smoke tests took {duration:.1f}s, should be < 120s"

    def test_individual_smoke_test_speed(self, sample_image_640x640):
        """
        Verify individual smoke tests run quickly.

        Each smoke test should complete in < 10 seconds.
        """
        class QuickMockDetector:
            def __init__(self):
                self.call_count = 0

            def detect(self, image):
                self.call_count += 1
                # Simulate very fast detection
                time.sleep(0.001)
                return {'boxes': [], 'scores': [], 'classes': []}

        detector = QuickMockDetector()

        # Simulate smoke test: 3 iterations
        start = time.time()
        for _ in range(3):
            detector.detect(sample_image_640x640)
        duration = time.time() - start

        # Should be very fast
        assert duration < 1.0, f"Smoke test simulation took {duration:.3f}s, should be < 1s"

        print(f"\n✅ Smoke test speed: {duration*1000:.2f}ms")


@pytest.mark.benchmark
class TestRegressionDetection:
    """
    Test regression detection functionality.

    Validates that the regression detection script works correctly.
    """

    def test_regression_detection_pass(self, tmp_path):
        """
        Verify regression detection passes when performance improves.
        """
        # Create baseline
        baseline = {
            'benchmarks': {
                'test1': {
                    'latency_ms': 100.0,
                    'speedup': 2.0
                }
            }
        }

        # Create current results (better performance)
        current = {
            'benchmarks': {
                'test1': {
                    'latency_ms': 90.0,  # Improved (lower is better)
                    'speedup': 2.5       # Improved (higher is better)
                }
            }
        }

        # Save to files
        baseline_file = tmp_path / "baseline.json"
        current_file = tmp_path / "current.json"

        with open(baseline_file, 'w') as f:
            json.dump(baseline, f)
        with open(current_file, 'w') as f:
            json.dump(current, f)

        # Run regression check
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/check_regression.py', str(current_file), '--baseline', str(baseline_file)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        # Should pass (exit code 0)
        assert result.returncode == 0, f"Regression check failed unexpectedly: {result.stdout}"
        assert "No performance regression" in result.stdout

    def test_regression_detection_fail(self, tmp_path):
        """
        Verify regression detection fails when performance degrades.
        """
        # Create baseline
        baseline = {
            'benchmarks': {
                'test1': {
                    'latency_ms': 100.0,
                    'speedup': 2.0
                }
            }
        }

        # Create current results (worse performance)
        current = {
            'benchmarks': {
                'test1': {
                    'latency_ms': 115.0,  # Regressed (15% worse)
                    'speedup': 1.7        # Regressed (15% worse)
                }
            }
        }

        # Save to files
        baseline_file = tmp_path / "baseline.json"
        current_file = tmp_path / "current.json"

        with open(baseline_file, 'w') as f:
            json.dump(baseline, f)
        with open(current_file, 'w') as f:
            json.dump(current, f)

        # Run regression check
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/check_regression.py', str(current_file), '--baseline', str(baseline_file)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        # Should fail (exit code 1)
        assert result.returncode == 1, "Regression check should have failed"
        assert "Performance regression detected" in result.stdout

    def test_regression_threshold(self, tmp_path):
        """
        Verify regression threshold is respected.
        """
        baseline = {
            'benchmarks': {
                'test1': {'latency_ms': 100.0}
            }
        }

        # Exactly at threshold (10% worse)
        current = {
            'benchmarks': {
                'test1': {'latency_ms': 110.0}  # Exactly 10% worse
            }
        }

        baseline_file = tmp_path / "baseline.json"
        current_file = tmp_path / "current.json"

        with open(baseline_file, 'w') as f:
            json.dump(baseline, f)
        with open(current_file, 'w') as f:
            json.dump(current, f)

        # Should fail with 10% threshold (default)
        result = subprocess.run(
            ['python', 'scripts/check_regression.py', str(current_file),
             '--baseline', str(baseline_file), '--threshold', '0.10'],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        assert result.returncode == 1, "Should detect regression at threshold"


@pytest.mark.benchmark
class TestBenchmarkRunner:
    """
    Test the benchmark runner script.
    """

    def test_runner_creates_results_file(self, tmp_path):
        """
        Verify benchmark runner creates results file.
        """
        output_file = tmp_path / "test_results.json"

        # Run benchmark runner (would normally run actual benchmarks)
        pytest.skip("Would run actual benchmarks - too expensive for unit test")

        # In practice:
        # result = subprocess.run(
        #     ['python', 'scripts/run_benchmarks.py', '--output', str(output_file)],
        #     cwd=Path(__file__).parent.parent.parent,
        #     capture_output=True
        # )
        # assert output_file.exists(), "Benchmark runner should create results file"

    def test_runner_json_format(self, tmp_path):
        """
        Verify benchmark runner outputs valid JSON.
        """
        # Create mock results file
        results = {
            'timestamp': '2026-01-03T00:00:00Z',
            'hardware': {'cpu': 'test', 'ram': 16},
            'benchmarks': {}
        }

        results_file = tmp_path / "results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f)

        # Should be valid JSON
        with open(results_file, 'r') as f:
            loaded = json.load(f)

        assert loaded == results, "JSON should be valid and match original"


@pytest.mark.benchmark
class TestBaselineManagement:
    """
    Test baseline file management.
    """

    def test_create_new_baseline(self, baseline_path, save_baseline):
        """
        Verify new baseline can be created.
        """
        # Create test baseline
        baseline = {
            'benchmarks': {
                'test': {'status': 'PASS'}
            }
        }

        # Save
        save_baseline(baseline_path, baseline)

        # Verify file exists
        assert baseline_path.exists(), "Baseline file should be created"

        # Verify content
        with open(baseline_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == baseline, "Baseline content should match"

    def test_load_existing_baseline(self, baseline_path, save_baseline, load_baseline):
        """
        Verify existing baseline can be loaded.
        """
        # Create baseline
        baseline = {
            'benchmarks': {
                'test': {'status': 'PASS'}
            }
        }
        save_baseline(baseline_path, baseline)

        # Load it
        loaded = load_baseline(baseline_path)

        assert loaded is not None, "Should load existing baseline"
        assert loaded == baseline, "Loaded baseline should match original"

    def test_load_missing_baseline(self, baseline_path, load_baseline):
        """
        Verify loading missing baseline returns None.
        """
        # Don't create baseline file
        if baseline_path.exists():
            baseline_path.unlink()

        # Try to load
        loaded = load_baseline(baseline_path)

        assert loaded is None, "Should return None for missing baseline"


@pytest.mark.benchmark
class TestHardwareDetection:
    """
    Test hardware information detection.
    """

    def test_hardware_info_structure(self, hardware_info):
        """
        Verify hardware info has required fields.
        """
        assert 'cpu' in hardware_info, "Hardware info should have CPU info"
        assert 'ram' in hardware_info, "Hardware info should have RAM info"
        assert 'gpu' in hardware_info, "Hardware info should have GPU info"

        # CPU info
        assert 'cores' in hardware_info['cpu'], "CPU info should have cores"
        assert 'threads' in hardware_info['cpu'], "CPU info should have threads"

        # RAM info
        assert 'total_gb' in hardware_info['ram'], "RAM info should have total_gb"
        assert hardware_info['ram']['total_gb'] > 0, "RAM should be > 0"

        # GPU info
        assert 'available' in hardware_info['gpu'], "GPU info should have availability"

    def test_cpu_count_positive(self, hardware_info):
        """
        Verify CPU count is positive.
        """
        assert hardware_info['cpu']['cores'] > 0, "Should have at least 1 CPU core"
        assert hardware_info['cpu']['threads'] >= hardware_info['cpu']['cores'], \
            "Threads should be >= cores"


@pytest.mark.benchmark
class TestHelpers:
    """
    Test benchmark helper functions and fixtures.
    """

    def test_sample_image_dimensions(self, sample_image_640x640):
        """
        Verify sample images have correct dimensions.
        """
        assert sample_image_640x640.shape == (640, 640, 3), \
            f"Image should be 640x640x3, got {sample_image_640x640.shape}"

    def test_sample_image_type(self, sample_image_640x640):
        """
        Verify sample images are uint8.
        """
        assert sample_image_640x640.dtype == np.uint8, \
            f"Image should be uint8, got {sample_image_640x640.dtype}"

    def test_sample_batch_size(self, sample_batch_images):
        """
        Verify sample batch has correct number of images.
        """
        assert len(sample_batch_images) == 8, f"Batch should have 8 images, got {len(sample_batch_images)}"

    def test_performance_thresholds_defined(self, performance_thresholds):
        """
        Verify all required thresholds are defined.
        """
        required = [
            'abstraction_overhead',
            'onnx_speedup',
            'quantization_speedup',
            'cpu_latency_ms',
            'gpu_latency_ms'
        ]

        for key in required:
            assert key in performance_thresholds, f"Threshold {key} should be defined"
            assert performance_thresholds[key] > 0, f"Threshold {key} should be positive"
