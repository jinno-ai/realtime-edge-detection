"""
Metrics collector for detection performance monitoring.

This module implements the MetricsCollector class that tracks inference latency,
FPS, memory usage, GPU utilization, and error counts for detection operations.
"""

import time
import psutil
from typing import Optional, Dict, Any
from contextlib import contextmanager


class MetricsCollector:
    """
    Collects and tracks performance metrics for object detection.

    This class provides methods to record detection latency, calculate FPS,
    track memory usage, and monitor GPU utilization when available.

    Attributes:
        enabled: Whether metrics collection is enabled
        total_detections: Total number of detections performed
        total_errors: Total number of errors encountered
        inference_times: List of recent inference times (ms)
        fps_samples: List of recent FPS measurements
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the MetricsCollector.

        Args:
            enabled: Whether metrics collection is enabled (default: True)
        """
        self.enabled = enabled

        # Counters
        self._total_detections = 0
        self._total_errors = 0

        # Timing
        self._inference_start_time: Optional[float] = None
        self._inference_times = []

        # FPS tracking
        self._frame_count = 0
        self._fps_start_time: Optional[float] = None
        self._fps_samples = []

        # Memory tracking (MB)
        self._memory_samples = []

        # GPU tracking (if available)
        self._gpu_available = self._check_gpu_available()
        self._gpu_utilization_samples = []

    def _check_gpu_available(self) -> bool:
        """
        Check if GPU is available for monitoring.

        Returns:
            True if GPU is available, False otherwise
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @property
    def total_detections(self) -> int:
        """Get total number of detections."""
        return self._total_detections

    @property
    def total_errors(self) -> int:
        """Get total number of errors."""
        return self._total_errors

    @property
    def inference_times(self) -> list:
        """Get list of inference times in milliseconds."""
        return self._inference_times

    @property
    def fps_samples(self) -> list:
        """Get list of FPS samples."""
        return self._fps_samples

    def record_detection(self, inference_time_ms: float) -> None:
        """
        Record a detection with its inference time.

        Args:
            inference_time_ms: Inference time in milliseconds
        """
        if not self.enabled:
            return

        self._total_detections += 1
        self._inference_times.append(inference_time_ms)

        # Track FPS
        self._frame_count += 1
        if self._fps_start_time is None:
            self._fps_start_time = time.time()
        else:
            elapsed = time.time() - self._fps_start_time
            if elapsed > 0:
                fps = self._frame_count / elapsed
                self._fps_samples.append(fps)

    def record_error(self) -> None:
        """Record an error occurrence."""
        if not self.enabled:
            return

        self._total_errors += 1

    @contextmanager
    def measure_inference(self):
        """
        Context manager to measure inference time.

        Yields:
            None

        Example:
            >>> with collector.measure_inference():
            ...     result = detector.detect(image)
        """
        if not self.enabled:
            yield
            return

        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000.0
            self.record_detection(inference_time_ms)

    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.

        Returns:
            Memory usage in megabytes
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # Convert bytes to MB

    def get_gpu_utilization(self) -> Optional[Dict[str, float]]:
        """
        Get GPU utilization metrics.

        Returns:
            Dictionary with GPU utilization metrics, or None if GPU not available.
            Keys: 'utilization_percent', 'memory_used_mb', 'memory_total_mb'
        """
        if not self._gpu_available:
            return None

        try:
            import torch
            if not torch.cuda.is_available():
                return None

            # Get utilization for current device
            device_id = torch.cuda.current_device()

            # Memory info
            memory_allocated = torch.cuda.memory_allocated(device_id) / (1024 * 1024)  # MB
            memory_reserved = torch.cuda.memory_reserved(device_id) / (1024 * 1024)  # MB
            memory_total = torch.cuda.get_device_properties(device_id).total_memory / (1024 * 1024)  # MB

            return {
                'utilization_percent': (memory_allocated / memory_total * 100) if memory_total > 0 else 0,
                'memory_used_mb': memory_allocated,
                'memory_reserved_mb': memory_reserved,
                'memory_total_mb': memory_total
            }
        except Exception:
            return None

    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect all current metrics.

        Returns:
            Dictionary containing all collected metrics
        """
        if not self.enabled:
            return {}

        metrics = {}

        # Always include counts
        metrics['detection_total'] = self._total_detections
        metrics['errors_total'] = self._total_errors

        # Latency metrics
        if self._inference_times:
            metrics['latency_ms_count'] = len(self._inference_times)
            metrics['latency_ms_sum'] = sum(self._inference_times)
            metrics['latency_ms_avg'] = sum(self._inference_times) / len(self._inference_times)

        # FPS metrics
        if self._fps_samples:
            metrics['fps'] = self._fps_samples[-1] if self._fps_samples else 0

        # Memory metrics
        memory_mb = self.get_memory_usage_mb()
        metrics['memory_mb'] = memory_mb

        # GPU metrics
        gpu_metrics = self.get_gpu_utilization()
        if gpu_metrics:
            metrics['gpu_utilization_percent'] = gpu_metrics['utilization_percent']
            metrics['gpu_memory_used_mb'] = gpu_metrics['memory_used_mb']
            metrics['gpu_memory_total_mb'] = gpu_metrics['memory_total_mb']

        return metrics

    def reset(self) -> None:
        """Reset all metrics."""
        self._total_detections = 0
        self._total_errors = 0
        self._inference_times = []
        self._frame_count = 0
        self._fps_start_time = None
        self._fps_samples = []
        self._memory_samples = []
        self._gpu_utilization_samples = []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics summary of collected metrics.

        Returns:
            Dictionary with metrics statistics
        """
        if not self.enabled or not self._inference_times:
            return {
                'total_detections': 0,
                'total_errors': 0,
                'avg_inference_time_ms': 0,
                'min_inference_time_ms': 0,
                'max_inference_time_ms': 0,
                'fps': 0,
                'memory_mb': self.get_memory_usage_mb()
            }

        return {
            'total_detections': self._total_detections,
            'total_errors': self._total_errors,
            'avg_inference_time_ms': sum(self._inference_times) / len(self._inference_times),
            'min_inference_time_ms': min(self._inference_times),
            'max_inference_time_ms': max(self._inference_times),
            'fps': self._fps_samples[-1] if self._fps_samples else 0,
            'memory_mb': self.get_memory_usage_mb()
        }
