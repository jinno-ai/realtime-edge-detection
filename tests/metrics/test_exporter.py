"""
Tests for PrometheusExporter class.
"""

import pytest
import time
import threading
from src.metrics.exporter import PrometheusExporter


class TestPrometheusExporter:
    """Test suite for PrometheusExporter."""

    def test_initialization(self):
        """Test exporter initialization."""
        exporter = PrometheusExporter(port=9091)
        assert exporter.port == 9091
        assert exporter.host == '0.0.0.0'
        assert exporter._server is None

    def test_metrics_setup(self):
        """Test that all metrics are properly set up."""
        exporter = PrometheusExporter(port=9091)

        # Check that all metrics exist
        assert exporter.detection_latency_ms is not None
        assert exporter.detection_fps is not None
        assert exporter.detection_memory_mb is not None
        assert exporter.detection_total is not None
        assert exporter.detection_errors_total is not None
        assert exporter.gpu_utilization_percent is not None
        assert exporter.gpu_memory_used_mb is not None

    def test_record_detection(self):
        """Test recording a detection."""
        exporter = PrometheusExporter(port=9091)

        # Record detection
        exporter.record_detection(50.0)

        # Metrics text should contain the detection
        metrics_text = exporter.get_metrics_text()
        assert b'detection_latency_ms_bucket' in metrics_text or b'detection_total' in metrics_text

    def test_record_multiple_detections(self):
        """Test recording multiple detections."""
        exporter = PrometheusExporter(port=9091)

        exporter.record_detection(50.0)
        exporter.record_detection(60.0)
        exporter.record_detection(70.0)

        metrics_text = exporter.get_metrics_text()
        assert metrics_text is not None
        assert len(metrics_text) > 0

    def test_record_error(self):
        """Test recording an error."""
        exporter = PrometheusExporter(port=9091)

        exporter.record_error()

        metrics_text = exporter.get_metrics_text()
        assert b'detection_errors_total' in metrics_text

    def test_set_fps(self):
        """Test setting FPS."""
        exporter = PrometheusExporter(port=9091)

        exporter.set_fps(30.5)

        metrics_text = exporter.get_metrics_text()
        assert b'detection_fps' in metrics_text
        assert b'30.5' in metrics_text or b'30' in metrics_text

    def test_set_memory_mb(self):
        """Test setting memory usage."""
        exporter = PrometheusExporter(port=9091)

        exporter.set_memory_mb(512.5)

        metrics_text = exporter.get_metrics_text()
        assert b'detection_memory_mb' in metrics_text

    def test_set_gpu_utilization(self):
        """Test setting GPU utilization."""
        exporter = PrometheusExporter(port=9091)

        exporter.set_gpu_utilization(85.5, 2048.0)

        metrics_text = exporter.get_metrics_text()
        assert b'detection_gpu_utilization_percent' in metrics_text
        assert b'detection_gpu_memory_used_mb' in metrics_text

    def test_get_metrics_text(self):
        """Test getting metrics in Prometheus text format."""
        exporter = PrometheusExporter(port=9091)

        exporter.record_detection(50.0)
        exporter.set_fps(30.0)
        exporter.set_memory_mb(512.0)

        metrics_text = exporter.get_metrics_text()

        assert isinstance(metrics_text, bytes)
        assert len(metrics_text) > 0
        assert b'# HELP' in metrics_text or b'# TYPE' in metrics_text

    def test_get_content_type(self):
        """Test getting content type."""
        exporter = PrometheusExporter(port=9091)

        content_type = exporter.get_content_type()

        assert content_type is not None
        assert 'text/plain' in content_type or 'prometheus' in content_type.lower()

    def test_start_server(self):
        """Test starting the HTTP server."""
        exporter = PrometheusExporter(port=9092)

        try:
            exporter.start_server()

            # Server should be running
            assert exporter._server is not None

            # Give it a moment to start
            time.sleep(0.1)

        finally:
            exporter.stop_server()

    def test_start_server_already_running(self):
        """Test that starting server twice raises error."""
        exporter = PrometheusExporter(port=9093)

        try:
            exporter.start_server()
            time.sleep(0.1)

            # Should raise error when trying to start again
            with pytest.raises(RuntimeError):
                exporter.start_server()

        finally:
            exporter.stop_server()

    def test_stop_server(self):
        """Test stopping the HTTP server."""
        exporter = PrometheusExporter(port=9094)

        exporter.start_server()
        time.sleep(0.1)

        exporter.stop_server()

        # Server reference should be cleared
        assert exporter._server is None

    def test_context_manager(self):
        """Test using exporter as context manager."""
        with PrometheusExporter(port=9095) as exporter:
            exporter.record_detection(50.0)
            time.sleep(0.1)

            # Server should be running
            assert exporter._server is not None

        # Server should be stopped after context
        assert exporter._server is None

    def test_create_handler(self):
        """Test creating WSGI handler."""
        exporter = PrometheusExporter(port=9091)

        handler = exporter.create_handler()

        assert handler is not None
        assert callable(handler)

        # Test handler with mock environ
        environ = {
            'PATH_INFO': '/metrics',
            'REQUEST_METHOD': 'GET'
        }

        response = []

        def start_response(status, headers):
            response.append((status, headers))

        result = handler(environ, start_response)

        assert len(result) > 0
        assert response[0][0] == '200 OK'

    def test_create_handler_404(self):
        """Test handler returns 404 for wrong path."""
        exporter = PrometheusExporter(port=9091)

        handler = exporter.create_handler()

        environ = {
            'PATH_INFO': '/wrong_path',
            'REQUEST_METHOD': 'GET'
        }

        response = []

        def start_response(status, headers):
            response.append((status, headers))

        result = handler(environ, start_response)

        assert response[0][0] == '404 Not Found'

    def test_update_from_collector(self):
        """Test updating metrics from collector data."""
        exporter = PrometheusExporter(port=9091)

        collector_metrics = {
            'fps': 30.0,
            'memory_mb': 512.0,
            'gpu_utilization_percent': 85.0,
            'gpu_memory_used_mb': 2048.0
        }

        exporter.update_from_collector(collector_metrics)

        metrics_text = exporter.get_metrics_text()
        assert b'detection_fps' in metrics_text
        assert b'detection_memory_mb' in metrics_text
