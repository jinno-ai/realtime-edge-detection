"""
Performance test fixtures and configuration.
"""

import pytest
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any
import time
import psutil
import os


# Performance thresholds from NFR requirements
PERFORMANCE_THRESHOLDS = {
    'abstraction_overhead': 0.05,  # 5% max overhead
    'onnx_speedup': 1.5,           # 1.5x min speedup
    'quantization_speedup': 2.0,   # 2x min speedup
    'quantization_accuracy_loss': 0.02,  # 2% max accuracy loss
    'async_speedup': 1.5,          # 1.5x min speedup
    'cpu_latency_ms': 30,          # NFR-P1
    'gpu_latency_ms': 10,          # NFR-P2
    'fps': 30,                     # NFR-P3
    'memory_mb': 500               # NFR-P4
}


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for validation."""
    return PERFORMANCE_THRESHOLDS.copy()


@pytest.fixture
def sample_image_640x640():
    """Create a sample 640x640 RGB image for testing."""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_1280x720():
    """Create a sample 1280x720 HD RGB image for testing."""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_batch_images():
    """Create a batch of sample images for batch processing tests."""
    return [
        np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        for _ in range(8)
    ]


@pytest.fixture
def temp_model_path(tmp_path):
    """Create a temporary path for model files."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def warmup_iterations():
    """Number of warmup iterations before benchmarking."""
    return 3


@pytest.fixture
def benchmark_iterations():
    """Number of benchmark iterations for measurement."""
    return 10


@pytest.fixture
def hardware_info():
    """Get current hardware information."""
    import platform

    info = {
        'cpu': {
            'platform': platform.machine(),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'frequency_max': psutil.cpu_freq().max if psutil.cpu_freq() else None,
        },
        'ram': {
            'total_gb': psutil.virtual_memory().total / (1024**3),
            'available_gb': psutil.virtual_memory().available / (1024**3),
        },
        'gpu': {
            'available': torch.cuda.is_available(),
            'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        'platform': platform.system(),
        'python_version': platform.python_version(),
    }

    return info


@pytest.fixture
def measure_latency():
    """Helper function to measure latency of detection calls."""
    def _measure_latency(detector, image, iterations=10, warmup=3):
        """
        Measure detection latency.

        Args:
            detector: Detector instance with detect() method
            image: Input image
            iterations: Number of measurement iterations
            warmup: Number of warmup iterations

        Returns:
            Dict with latency statistics (ms)
        """
        # Warmup
        for _ in range(warmup):
            _ = detector.detect(image)

        # Measure
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = detector.detect(image)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        return {
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'std': np.std(latencies),
            'min': np.min(latencies),
            'max': np.max(latencies),
            'values': latencies,
        }

    return _measure_latency


@pytest.fixture
def measure_memory():
    """Helper function to measure memory usage."""
    def _measure_memory(detector, image):
        """
        Measure memory usage of detection.

        Args:
            detector: Detector instance
            image: Input image

        Returns:
            Memory usage in MB
        """
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Run detection
        _ = detector.detect(image)

        mem_after = process.memory_info().rss / (1024 * 1024)  # MB

        return {
            'before_mb': mem_before,
            'after_mb': mem_after,
            'used_mb': mem_after - mem_before,
            'peak_mb': mem_after,  # Simplified
        }

    return _measure_memory


@pytest.fixture
def measure_throughput():
    """Helper function to measure throughput."""
    def _measure_throughput(detector, images, duration_sec=5.0):
        """
        Measure detection throughput.

        Args:
            detector: Detector instance
            images: List of input images
            duration_sec: Duration to measure (seconds)

        Returns:
            Dict with throughput metrics
        """
        start_time = time.time()
        count = 0

        while time.time() - start_time < duration_sec:
            for img in images:
                _ = detector.detect(img)
                count += 1

            if time.time() - start_time >= duration_sec:
                break

        elapsed = time.time() - start_time
        fps = count / elapsed if elapsed > 0 else 0

        return {
            'total_detections': count,
            'elapsed_sec': elapsed,
            'fps': fps,
            'avg_latency_ms': (elapsed / count) * 1000 if count > 0 else 0,
        }

    return _measure_throughput


@pytest.fixture
def baseline_path():
    """Path to baseline measurements file."""
    return Path(__file__).parent.parent.parent / "baselines" / "performance_baseline.json"


@pytest.fixture
def load_baseline():
    """Helper function to load baseline measurements."""
    def _load_baseline(baseline_file):
        """Load baseline from JSON file."""
        import json
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return None

    return _load_baseline


@pytest.fixture
def save_baseline():
    """Helper function to save baseline measurements."""
    def _save_baseline(baseline_file, data):
        """Save baseline to JSON file."""
        import json
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_file, 'w') as f:
            json.dump(data, f, indent=2)

    return _save_baseline


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (quick performance check)"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as detailed benchmark"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (runs > 1 minute)"
    )
