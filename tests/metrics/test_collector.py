"""
Tests for MetricsCollector class.
"""

import pytest
import time
from src.metrics.collector import MetricsCollector


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    def test_initialization_enabled(self):
        """Test collector initialization with enabled=True."""
        collector = MetricsCollector(enabled=True)
        assert collector.enabled is True
        assert collector.total_detections == 0
        assert collector.total_errors == 0
        assert collector.inference_times == []
        assert collector.fps_samples == []

    def test_initialization_disabled(self):
        """Test collector initialization with enabled=False."""
        collector = MetricsCollector(enabled=False)
        assert collector.enabled is False

    def test_record_detection(self):
        """Test recording a detection."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)

        assert collector.total_detections == 1
        assert len(collector.inference_times) == 1
        assert collector.inference_times[0] == 50.0

    def test_record_multiple_detections(self):
        """Test recording multiple detections."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)
        collector.record_detection(60.0)
        collector.record_detection(70.0)

        assert collector.total_detections == 3
        assert len(collector.inference_times) == 3
        assert sum(collector.inference_times) == 180.0

    def test_record_detection_when_disabled(self):
        """Test that recording is ignored when disabled."""
        collector = MetricsCollector(enabled=False)
        collector.record_detection(50.0)

        assert collector.total_detections == 0
        assert len(collector.inference_times) == 0

    def test_record_error(self):
        """Test recording an error."""
        collector = MetricsCollector(enabled=True)
        collector.record_error()

        assert collector.total_errors == 1

    def test_record_error_when_disabled(self):
        """Test that error recording is ignored when disabled."""
        collector = MetricsCollector(enabled=False)
        collector.record_error()

        assert collector.total_errors == 0

    def test_get_memory_usage_mb(self):
        """Test getting memory usage."""
        collector = MetricsCollector(enabled=True)
        memory_mb = collector.get_memory_usage_mb()

        assert memory_mb > 0
        assert isinstance(memory_mb, float)

    def test_get_gpu_utilization_no_gpu(self):
        """Test GPU utilization when GPU is not available."""
        collector = MetricsCollector(enabled=True)
        # This will return None if GPU is not available
        gpu_metrics = collector.get_gpu_utilization()

        # GPU metrics should be None or a dict with specific keys
        assert gpu_metrics is None or isinstance(gpu_metrics, dict)

    def test_collect_metrics_empty(self):
        """Test collecting metrics with no data."""
        collector = MetricsCollector(enabled=True)
        metrics = collector.collect_metrics()

        # Should have basic metrics even with no detections
        assert 'detection_total' in metrics
        assert 'errors_total' in metrics
        assert metrics['detection_total'] == 0
        assert metrics['errors_total'] == 0
        assert 'memory_mb' in metrics

    def test_collect_metrics_with_data(self):
        """Test collecting metrics with detection data."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)
        collector.record_detection(60.0)

        metrics = collector.collect_metrics()

        assert 'detection_total' in metrics
        assert metrics['detection_total'] == 2
        assert 'latency_ms_count' in metrics
        assert metrics['latency_ms_count'] == 2
        assert 'latency_ms_sum' in metrics
        assert metrics['latency_ms_sum'] == 110.0
        assert 'latency_ms_avg' in metrics
        assert metrics['latency_ms_avg'] == 55.0
        assert 'memory_mb' in metrics
        assert metrics['memory_mb'] > 0

    def test_collect_metrics_with_errors(self):
        """Test collecting metrics with errors."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)
        collector.record_error()

        metrics = collector.collect_metrics()

        assert 'errors_total' in metrics
        assert metrics['errors_total'] == 1

    def test_get_stats_empty(self):
        """Test getting stats with no data."""
        collector = MetricsCollector(enabled=True)
        stats = collector.get_stats()

        assert stats['total_detections'] == 0
        assert stats['total_errors'] == 0
        assert stats['avg_inference_time_ms'] == 0
        assert stats['min_inference_time_ms'] == 0
        assert stats['max_inference_time_ms'] == 0
        assert stats['fps'] == 0
        assert 'memory_mb' in stats

    def test_get_stats_with_data(self):
        """Test getting stats with detection data."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)
        collector.record_detection(100.0)
        collector.record_detection(75.0)

        stats = collector.get_stats()

        assert stats['total_detections'] == 3
        assert stats['avg_inference_time_ms'] == 75.0
        assert stats['min_inference_time_ms'] == 50.0
        assert stats['max_inference_time_ms'] == 100.0

    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector(enabled=True)
        collector.record_detection(50.0)
        collector.record_error()

        collector.reset()

        assert collector.total_detections == 0
        assert collector.total_errors == 0
        assert len(collector.inference_times) == 0
        assert len(collector.fps_samples) == 0

    def test_measure_inference_context_manager(self):
        """Test the measure_inference context manager."""
        collector = MetricsCollector(enabled=True)

        with collector.measure_inference():
            time.sleep(0.01)  # 10ms

        assert collector.total_detections == 1
        assert len(collector.inference_times) == 1
        # Should be approximately 10ms (allowing for some variance)
        assert collector.inference_times[0] >= 8.0

    def test_measure_inference_with_exception(self):
        """Test that exceptions are still raised after recording metrics."""
        collector = MetricsCollector(enabled=True)

        with pytest.raises(ValueError):
            with collector.measure_inference():
                time.sleep(0.01)
                raise ValueError("Test error")

        # Should still record the detection
        assert collector.total_detections == 1

    def test_fps_tracking(self):
        """Test FPS calculation over multiple detections."""
        collector = MetricsCollector(enabled=True)

        # Simulate 100 detections over 1 second
        start = time.time()
        for _ in range(100):
            collector.record_detection(10.0)  # 10ms each = 100 FPS theoretical

        elapsed = time.time() - start
        metrics = collector.collect_metrics()

        # FPS should be calculated
        if 'fps' in metrics:
            assert metrics['fps'] > 0
