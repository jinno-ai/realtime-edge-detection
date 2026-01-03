"""
Integrated metrics manager that combines CLI and Prometheus metrics.

This module provides a unified interface for metrics collection that supports
both the existing CLI MetricsTracker and the new Prometheus exporter.
"""

from typing import Optional, Dict, Any
from src.metrics.collector import MetricsCollector
from src.metrics.exporter import PrometheusExporter
from src.cli.metrics import MetricsTracker as CLIMetricsTracker


class MetricsManager:
    """
    Unified metrics manager supporting both CLI and Prometheus metrics.

    This class integrates MetricsCollector for internal metrics tracking
    and PrometheusExporter for external metrics exposure.

    Attributes:
        mode: Metrics mode ('none', 'prometheus', 'both')
        collector: Internal metrics collector
        exporter: Optional Prometheus exporter
        cli_tracker: Legacy CLI metrics tracker
    """

    def __init__(self, mode: str = 'none', prometheus_port: int = 9090):
        """
        Initialize the MetricsManager.

        Args:
            mode: Metrics collection mode ('none', 'prometheus', 'both')
            prometheus_port: Port for Prometheus metrics server (default: 9090)
        """
        self.mode = mode
        self.prometheus_port = prometheus_port

        # Initialize collector based on mode
        enabled = (mode != 'none')
        self.collector = MetricsCollector(enabled=enabled)

        # Initialize Prometheus exporter if needed
        self.exporter: Optional[PrometheusExporter] = None
        if mode == 'prometheus' or mode == 'both':
            self.exporter = PrometheusExporter(port=prometheus_port)

        # Initialize CLI tracker for backward compatibility
        self.cli_tracker = CLIMetricsTracker()

    def start_inference(self):
        """Start inference timing (CLI tracker compatibility)."""
        self.cli_tracker.start_inference()

    def end_inference(self) -> float:
        """
        End inference timing and record metrics.

        Returns:
            Inference time in seconds
        """
        elapsed = self.cli_tracker.end_inference()

        # Record in collector and Prometheus
        if self.mode != 'none':
            latency_ms = elapsed * 1000.0
            self.collector.record_detection(latency_ms)

            if self.exporter:
                self.exporter.record_detection(latency_ms)
                self._update_gauges()

        return elapsed

    def record_error(self):
        """Record a detection error."""
        if self.mode != 'none':
            self.collector.record_error()
            if self.exporter:
                self.exporter.record_error()

    def _update_gauges(self):
        """Update Prometheus gauges from collector metrics."""
        if not self.exporter:
            return

        metrics = self.collector.collect_metrics()

        # Update FPS
        if 'fps' in metrics:
            self.exporter.set_fps(metrics['fps'])

        # Update memory
        if 'memory_mb' in metrics:
            self.exporter.set_memory_mb(metrics['memory_mb'])

        # Update GPU metrics
        if 'gpu_utilization_percent' in metrics and 'gpu_memory_used_mb' in metrics:
            self.exporter.set_gpu_utilization(
                metrics['gpu_utilization_percent'],
                metrics['gpu_memory_used_mb']
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics from CLI tracker.

        Returns:
            Dictionary with CLI statistics
        """
        return self.cli_tracker.get_stats()

    def format_stats(self, stats: Dict) -> str:
        """
        Format statistics for display.

        Args:
            stats: Statistics dictionary

        Returns:
            Formatted string
        """
        return self.cli_tracker.format_stats(stats)

    def start_prometheus_server(self):
        """Start the Prometheus metrics server."""
        if self.exporter:
            self.exporter.start_server()

    def stop_prometheus_server(self):
        """Stop the Prometheus metrics server."""
        if self.exporter:
            self.exporter.stop_server()

    def cleanup(self):
        """Cleanup resources."""
        self.stop_prometheus_server()

    def __enter__(self):
        """Context manager entry."""
        self.start_prometheus_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
