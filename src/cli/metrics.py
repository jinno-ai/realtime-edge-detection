"""
Performance metrics tracking for CLI operations.

This module provides metrics collection and display for detection operations,
including inference time, FPS, and memory usage.
"""

import time
import psutil
from typing import Dict, List


class MetricsTracker:
    """Track and display performance metrics for detection operations."""

    def __init__(self):
        """Initialize metrics tracker."""
        self.start_time = None
        self.inference_times = []
        self.detection_counts = []

    def start_inference(self):
        """Start inference timer."""
        self.start_time = time.time()

    def end_inference(self, detection_count: int = 0) -> float:
        """
        End inference and return elapsed time.

        Args:
            detection_count: Number of detections in this inference

        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0.0

        elapsed = time.time() - self.start_time
        self.inference_times.append(elapsed)
        if detection_count > 0:
            self.detection_counts.append(detection_count)

        self.start_time = None
        return elapsed

    def get_stats(self) -> Dict:
        """
        Calculate statistics from collected metrics.

        Returns:
            Dictionary with performance statistics
        """
        if not self.inference_times:
            return {
                'inference_time_ms': 0.0,
                'fps': 0.0,
                'detection_count': 0,
                'memory_mb': 0.0,
                'avg_inference_time_ms': 0.0,
                'total_inferences': 0
            }

        avg_time = sum(self.inference_times) / len(self.inference_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        memory_mb = psutil.virtual_memory().used / (1024 * 1024)
        total_detections = sum(self.detection_counts) if self.detection_counts else 0

        return {
            'inference_time_ms': avg_time * 1000,
            'fps': fps,
            'detection_count': total_detections,
            'memory_mb': memory_mb,
            'avg_inference_time_ms': avg_time * 1000,
            'total_inferences': len(self.inference_times)
        }

    def format_stats(self, stats: Dict) -> str:
        """
        Format statistics for display.

        Args:
            stats: Statistics dictionary from get_stats()

        Returns:
            Formatted string for display
        """
        if stats['total_inferences'] == 0:
            return "No detections performed"

        return (
            f"Detected {stats['detection_count']} objects "
            f"in {stats['inference_time_ms']:.1f}ms "
            f"({stats['fps']:.1f} FPS)"
        )

    def reset(self):
        """Reset all metrics."""
        self.start_time = None
        self.inference_times = []
        self.detection_counts = []
