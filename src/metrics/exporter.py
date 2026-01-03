"""
Prometheus metrics exporter.

This module implements the PrometheusExporter class that exposes metrics
on an HTTP endpoint for Prometheus scraping.
"""

import threading
import time
from typing import Optional, Dict, Any
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from prometheus_client.exposition import ThreadingWSGIServer


class PrometheusExporter:
    """
    Exports metrics via Prometheus HTTP endpoint.

    This class manages Prometheus metrics and runs an HTTP server
    to expose metrics for scraping.

    Attributes:
        host: Host to bind the metrics server to
        port: Port to bind the metrics server to
        registry: Prometheus collector registry
    """

    def __init__(
        self,
        port: int = 9090,
        host: str = '0.0.0.0',
        registry: Optional[CollectorRegistry] = None
    ):
        """
        Initialize the PrometheusExporter.

        Args:
            port: Port to expose metrics on (default: 9090)
            host: Host to bind to (default: '0.0.0.0')
            registry: Custom collector registry (default: None creates new)
        """
        self.port = port
        self.host = host
        self.registry = registry or CollectorRegistry()
        self._server: Optional[ThreadingWSGIServer] = None
        self._server_thread: Optional[threading.Thread] = None

        # Define Prometheus metrics
        self._setup_metrics()

    def _setup_metrics(self):
        """Setup Prometheus metrics with appropriate labels and buckets."""

        # Histogram: detection latency in milliseconds
        # Buckets: [10, 25, 50, 100, 250, 500] ms
        self.detection_latency_ms = Histogram(
            'detection_latency_ms',
            'Detection inference latency in milliseconds',
            buckets=[10, 25, 50, 100, 250, 500, float('inf')],
            registry=self.registry
        )

        # Gauge: current FPS
        self.detection_fps = Gauge(
            'detection_fps',
            'Current detection frames per second',
            registry=self.registry
        )

        # Gauge: current memory usage in MB
        self.detection_memory_mb = Gauge(
            'detection_memory_mb',
            'Current memory usage in megabytes',
            registry=self.registry
        )

        # Counter: total detections
        self.detection_total = Counter(
            'detection_total',
            'Total number of detections performed',
            registry=self.registry
        )

        # Counter: total errors
        self.detection_errors_total = Counter(
            'detection_errors_total',
            'Total number of detection errors',
            registry=self.registry
        )

        # GPU metrics (optional, only set if GPU available)
        self.gpu_utilization_percent = Gauge(
            'detection_gpu_utilization_percent',
            'GPU utilization percentage',
            registry=self.registry
        )

        self.gpu_memory_used_mb = Gauge(
            'detection_gpu_memory_used_mb',
            'GPU memory used in megabytes',
            registry=self.registry
        )

    def update_from_collector(self, metrics: Dict[str, Any]) -> None:
        """
        Update Prometheus metrics from collector data.

        Args:
            metrics: Dictionary of metrics from MetricsCollector
        """
        # Update detection total
        if 'detection_total' in metrics:
            # Counter doesn't have set(), we need to increment
            # This is handled by the collector recording directly
            pass

        # Update errors total
        if 'errors_total' in metrics:
            # Same as above
            pass

        # Update latency histogram
        if 'latency_ms_sum' in metrics and 'latency_ms_count' in metrics:
            # Histogram is updated incrementally, not from summary
            pass

        # Update FPS gauge
        if 'fps' in metrics:
            self.detection_fps.set(metrics['fps'])

        # Update memory gauge
        if 'memory_mb' in metrics:
            self.detection_memory_mb.set(metrics['memory_mb'])

        # Update GPU metrics
        if 'gpu_utilization_percent' in metrics:
            self.gpu_utilization_percent.set(metrics['gpu_utilization_percent'])

        if 'gpu_memory_used_mb' in metrics:
            self.gpu_memory_used_mb.set(metrics['gpu_memory_used_mb'])

    def record_detection(self, latency_ms: float) -> None:
        """
        Record a single detection with its latency.

        Args:
            latency_ms: Inference time in milliseconds
        """
        self.detection_latency_ms.observe(latency_ms)
        self.detection_total.inc()

    def record_error(self) -> None:
        """Record a detection error."""
        self.detection_errors_total.inc()

    def set_fps(self, fps: float) -> None:
        """
        Set current FPS value.

        Args:
            fps: Current frames per second
        """
        self.detection_fps.set(fps)

    def set_memory_mb(self, memory_mb: float) -> None:
        """
        Set current memory usage.

        Args:
            memory_mb: Memory usage in megabytes
        """
        self.detection_memory_mb.set(memory_mb)

    def set_gpu_utilization(self, utilization_percent: float, memory_used_mb: float) -> None:
        """
        Set GPU utilization metrics.

        Args:
            utilization_percent: GPU utilization percentage
            memory_used_mb: GPU memory used in MB
        """
        self.gpu_utilization_percent.set(utilization_percent)
        self.gpu_memory_used_mb.set(memory_used_mb)

    def start_server(self) -> None:
        """
        Start the Prometheus metrics HTTP server.

        Raises:
            RuntimeError: If server is already running
        """
        if self._server is not None:
            raise RuntimeError("Prometheus server is already running")

        from prometheus_client.exposition import start_http_server

        try:
            # Start the HTTP server
            self._server = start_http_server(self.port, addr=self.host, registry=self.registry)
        except Exception as e:
            raise RuntimeError(f"Failed to start Prometheus server: {e}")

    def stop_server(self) -> None:
        """Stop the Prometheus metrics HTTP server."""
        if self._server is not None:
            # prometheus_client's start_http_server doesn't provide a clean way to stop
            # The server runs in a daemon thread and will stop when the process exits
            self._server = None
            self._server_thread = None

    def get_metrics_text(self) -> bytes:
        """
        Get metrics in Prometheus text format.

        Returns:
            Metrics as bytes in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """
        Get the content type for metrics endpoint.

        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST

    def create_handler(self):
        """
        Create a request handler for the metrics endpoint.

        Returns:
            Function that handles HTTP requests for metrics
        """
        def handler(environ, start_response):
            """WSGI application for serving metrics."""
            if environ['PATH_INFO'] != '/metrics':
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b'Not Found']

            output = self.get_metrics_text()
            start_response(
                '200 OK',
                [('Content-Type', self.get_content_type())]
            )
            return [output]

        return handler

    def __enter__(self):
        """Context manager entry."""
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_server()
