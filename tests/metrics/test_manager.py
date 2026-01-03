"""
Tests for MetricsManager class.
"""

import pytest
from src.metrics.manager import MetricsManager


class TestMetricsManager:
    """Test suite for MetricsManager."""

    def test_initialization_none_mode(self):
        """Test manager initialization with mode='none'."""
        manager = MetricsManager(mode='none')

        assert manager.mode == 'none'
        assert manager.collector.enabled is False
        assert manager.exporter is None

    def test_initialization_prometheus_mode(self):
        """Test manager initialization with mode='prometheus'."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9091)

        assert manager.mode == 'prometheus'
        assert manager.collector.enabled is True
        assert manager.exporter is not None
        assert manager.exporter.port == 9091

    def test_initialization_invalid_mode(self):
        """Test that invalid mode falls back to 'none'."""
        manager = MetricsManager(mode='invalid')
        # Should not raise, but exporter should be None
        assert manager.exporter is None

    def test_start_inference(self):
        """Test starting inference timing."""
        manager = MetricsManager(mode='none')

        manager.start_inference()

        # CLI tracker should have started timing
        assert manager.cli_tracker.start_time is not None

    def test_end_inference(self):
        """Test ending inference timing."""
        manager = MetricsManager(mode='none')

        manager.start_inference()
        elapsed = manager.end_inference()

        assert elapsed >= 0
        assert isinstance(elapsed, float)

    def test_end_inference_with_prometheus(self):
        """Test ending inference records to Prometheus."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9096)

        manager.start_inference()
        elapsed = manager.end_inference()

        assert elapsed >= 0

        # Check that metrics were recorded
        metrics_text = manager.exporter.get_metrics_text()
        assert b'detection_latency_ms' in metrics_text or b'detection_total' in metrics_text

    def test_record_error(self):
        """Test recording an error."""
        manager = MetricsManager(mode='none')

        manager.record_error()

        # Should not raise any errors

    def test_record_error_with_prometheus(self):
        """Test recording an error with Prometheus."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9097)

        manager.record_error()

        metrics_text = manager.exporter.get_metrics_text()
        assert b'detection_errors_total' in metrics_text

    def test_get_stats(self):
        """Test getting statistics."""
        manager = MetricsManager(mode='none')

        stats = manager.get_stats()

        assert isinstance(stats, dict)
        assert 'inference_time_ms' in stats
        assert 'fps' in stats
        assert 'total_inferences' in stats

    def test_format_stats(self):
        """Test formatting statistics."""
        manager = MetricsManager(mode='none')

        # Create some stats
        manager.start_inference()
        manager.end_inference()

        stats = manager.get_stats()
        formatted = manager.format_stats(stats)

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_start_prometheus_server(self):
        """Test starting Prometheus server."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9098)

        try:
            manager.start_prometheus_server()

            # Should not raise
            assert manager.exporter._server is not None

        finally:
            manager.stop_prometheus_server()

    def test_stop_prometheus_server(self):
        """Test stopping Prometheus server."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9099)

        manager.start_prometheus_server()
        manager.stop_prometheus_server()

        assert manager.exporter._server is None

    def test_cleanup(self):
        """Test cleanup method."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9100)

        manager.start_prometheus_server()
        manager.cleanup()

        assert manager.exporter._server is None

    def test_context_manager(self):
        """Test using manager as context manager."""
        with MetricsManager(mode='prometheus', prometheus_port=9101) as manager:
            assert manager.exporter._server is not None
            manager.start_inference()
            manager.end_inference()

        # Server should be stopped after context
        assert manager.exporter._server is None

    def test_integration_with_cli_tracker(self):
        """Test that manager maintains CLI tracker compatibility."""
        manager = MetricsManager(mode='none')

        # Simulate detection workflow
        manager.start_inference()
        elapsed = manager.end_inference()

        stats = manager.get_stats()

        assert stats['total_inferences'] == 1
        assert 'inference_time_ms' in stats

    def test_prometheus_metrics_collection(self):
        """Test that Prometheus metrics are collected."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9102)

        # Perform some detections
        manager.start_inference()
        manager.end_inference()

        manager.start_inference()
        manager.end_inference()

        # Check Prometheus metrics
        metrics_text = manager.exporter.get_metrics_text()
        assert len(metrics_text) > 0

    def test_disabled_prometheus_mode(self):
        """Test that disabled mode doesn't create exporter."""
        manager = MetricsManager(mode='none')

        manager.start_prometheus_server()  # Should do nothing
        manager.stop_prometheus_server()  # Should do nothing

        assert manager.exporter is None

    def test_custom_prometheus_port(self):
        """Test custom Prometheus port."""
        manager = MetricsManager(mode='prometheus', prometheus_port=9999)

        assert manager.exporter.port == 9999
