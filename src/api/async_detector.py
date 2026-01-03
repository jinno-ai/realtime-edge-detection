"""
AsyncDetector - Async and batch detection wrapper for efficient parallel processing.

Provides asynchronous detection interface using ThreadPoolExecutor for parallel
execution, enabling efficient video streaming and batch processing scenarios.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import List, Dict, Any, Optional, Tuple
from threading import Lock

import numpy as np

from src.detection.base import AbstractDetector, DetectionResult


class PartialBatchError(Exception):
    """
    Exception raised when batch detection partially fails.

    Attributes:
        message: Error message
        successful: Number of successfully processed images
        total: Total number of images
        results: Partial results (images that succeeded)
    """

    def __init__(
        self,
        message: str,
        successful: int,
        total: int,
        results: List[DetectionResult]
    ):
        super().__init__(message)
        self.successful = successful
        self.total = total
        self.results = results


class AsyncDetector:
    """
    Async wrapper for detectors with ThreadPoolExecutor-based parallel execution.

    Features:
    - Asynchronous detection API for non-blocking operations
    - Thread pool management for parallel execution
    - Optimized batch detection with automatic chunking
    - Error handling and propagation
    - Thread-safe operations

    Example:
        >>> from src.api import AsyncDetector
        >>> from src.detection.yolov8 import YOLOv8Detector
        >>>
        >>> # Create base detector
        >>> base_detector = YOLOv8Detector()
        >>> base_detector.load_model('yolov8n.pt', device='cuda')
        >>>
        >>> # Wrap with async interface
        >>> detector = AsyncDetector(base_detector, max_workers=4)
        >>>
        >>> # Async detection
        >>> import asyncio
        >>> async def process():
        ...     result = await detector.detect_async(image)
        ...     return result
        >>> asyncio.run(process())
        >>>
        >>> # Batch detection
        >>> results = detector.detect_batch(images, batch_size=16)
    """

    def __init__(
        self,
        detector: AbstractDetector,
        max_workers: int = 4,
        default_batch_size: int = 16
    ):
        """
        Initialize AsyncDetector.

        Args:
            detector: Base detector implementing AbstractDetector interface
            max_workers: Maximum number of parallel worker threads (default: 4)
            default_batch_size: Default batch size for batch processing (default: 16)

        Raises:
            ValueError: If detector is None or max_workers < 1
        """
        if detector is None:
            raise ValueError("Detector cannot be None")

        if max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {max_workers}")

        if default_batch_size < 1:
            raise ValueError(f"default_batch_size must be >= 1, got {default_batch_size}")

        self.detector = detector
        self.max_workers = max_workers
        self.default_batch_size = default_batch_size

        # Thread pool executor for parallel execution
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="detection_worker"
        )

        # Lock for thread-safe operations
        self._lock = Lock()

        # Track if detector has been shutdown
        self._shutdown = False

    async def detect_async(self, image: np.ndarray) -> DetectionResult:
        """
        Run asynchronous detection on a single image.

        Submits detection task to thread pool and awaits result without
        blocking the main thread.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format

        Returns:
            DetectionResult with boxes, scores, classes, and metadata

        Raises:
            RuntimeError: If detector has been shutdown
            ValueError: If image format is invalid
            Exception: Propagates detection errors from underlying detector

        Example:
            >>> result = await detector.detect_async(image)
            >>> print(f"Detected {result.metadata['num_detections']} objects")
        """
        if self._shutdown:
            raise RuntimeError("AsyncDetector has been shutdown")

        # Validate image format
        if not isinstance(image, np.ndarray):
            raise ValueError(f"Image must be numpy array, got {type(image)}")

        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Image must have shape (H, W, 3), got {image.shape}"
            )

        # Submit detection task to thread pool
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self.executor,
                self._detect_sync,
                image
            )
            return result
        except Exception as e:
            # Re-raise with context
            raise Exception(f"Async detection failed: {str(e)}") from e

    def detect_batch(
        self,
        images: List[np.ndarray],
        batch_size: Optional[int] = None
    ) -> List[DetectionResult]:
        """
        Run batch detection on multiple images with automatic chunking.

        Splits images into batches and processes them in parallel using the
        thread pool for maximum efficiency.

        Args:
            images: List of input images as numpy arrays (H, W, C) in RGB format
            batch_size: Batch size for processing (default: self.default_batch_size)

        Returns:
            List of DetectionResult objects, one per input image

        Raises:
            RuntimeError: If detector has been shutdown
            ValueError: If images list is empty or batch_size < 1
            PartialBatchError: If some images fail processing

        Example:
            >>> results = detector.detect_batch(images, batch_size=16)
            >>> print(f"Processed {len(results)} images")
        """
        if self._shutdown:
            raise RuntimeError("AsyncDetector has been shutdown")

        if not images:
            raise ValueError("Images list cannot be empty")

        if batch_size is None:
            batch_size = self.default_batch_size

        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")

        # Split images into batches
        batches = self._split_into_batches(images, batch_size)

        # Process batches in parallel
        all_results = []
        failed_batches = []

        for batch_idx, batch in enumerate(batches):
            try:
                # Submit batch processing to thread pool
                future = self.executor.submit(self._detect_batch_sync, batch)
                batch_results = future.result()

                all_results.extend(batch_results)

            except Exception as e:
                # Log failed batch
                failed_batches.append({
                    'batch_index': batch_idx,
                    'batch_size': len(batch),
                    'error': str(e)
                })

                # Try processing images individually
                for img in batch:
                    try:
                        result = self._detect_sync(img)
                        all_results.append(result)
                    except Exception as e2:
                        # Create empty result for failed image
                        all_results.append(self._create_empty_result())

        # Check if we had any failures
        if failed_batches:
            total_processed = len(all_results)
            raise PartialBatchError(
                f"Batch processing completed with {len(failed_batches)} failed batches. "
                f"{total_processed}/{len(images)} images processed successfully.",
                successful=total_processed,
                total=len(images),
                results=all_results
            )

        return all_results

    async def detect_batch_async(
        self,
        images: List[np.ndarray],
        batch_size: Optional[int] = None
    ) -> List[DetectionResult]:
        """
        Run asynchronous batch detection.

        Async version of detect_batch for use in async contexts.

        Args:
            images: List of input images as numpy arrays
            batch_size: Batch size for processing

        Returns:
            List of DetectionResult objects

        Example:
            >>> results = await detector.detect_batch_async(images, batch_size=16)
        """
        if self._shutdown:
            raise RuntimeError("AsyncDetector has been shutdown")

        if not images:
            raise ValueError("Images list cannot be empty")

        if batch_size is None:
            batch_size = self.default_batch_size

        # Split into batches
        batches = self._split_into_batches(images, batch_size)

        # Process batches asynchronously
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._detect_batch_sync, batch)
            for batch in batches
        ]

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                raise batch_result
            all_results.extend(batch_result)

        return all_results

    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool gracefully.

        Args:
            wait: Whether to wait for pending tasks to complete (default: True)

        Example:
            >>> detector.shutdown()
        """
        with self._lock:
            if not self._shutdown:
                self.executor.shutdown(wait=wait)
                self._shutdown = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.shutdown(wait=True)
        return False

    def _detect_sync(self, image: np.ndarray) -> DetectionResult:
        """
        Synchronous detection wrapper for thread pool execution.

        Args:
            image: Input image

        Returns:
            DetectionResult
        """
        return self.detector.detect(image)

    def _detect_batch_sync(self, images: List[np.ndarray]) -> List[DetectionResult]:
        """
        Synchronous batch detection wrapper for thread pool execution.

        Args:
            images: List of input images

        Returns:
            List of DetectionResult objects
        """
        return self.detector.detect_batch(images)

    def _split_into_batches(
        self,
        images: List[np.ndarray],
        batch_size: int
    ) -> List[List[np.ndarray]]:
        """
        Split images list into batches.

        Args:
            images: List of images
            batch_size: Batch size

        Returns:
            List of batches (each batch is a list of images)
        """
        batches = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            batches.append(batch)
        return batches

    def _create_empty_result(self) -> DetectionResult:
        """
        Create empty detection result for failed images.

        Returns:
            DetectionResult with no detections
        """
        return DetectionResult(
            boxes=np.empty((0, 4), dtype=np.float32),
            scores=np.empty((0,), dtype=np.float32),
            classes=np.empty((0,), dtype=np.int32),
            metadata={'num_detections': 0, 'error': True}
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get detector statistics.

        Returns:
            Dictionary with detector stats
        """
        return {
            'max_workers': self.max_workers,
            'default_batch_size': self.default_batch_size,
            'shutdown': self._shutdown,
            'detector_loaded': self.detector.is_loaded
        }


async def detect_multiple_async(
    detector: AsyncDetector,
    images: List[np.ndarray]
) -> List[DetectionResult]:
    """
    Detect multiple images in parallel using asyncio.gather.

    Utility function for concurrent detection of multiple images.

    Args:
        detector: AsyncDetector instance
        images: List of input images

    Returns:
        List of DetectionResult objects

    Example:
        >>> results = await detect_multiple_async(detector, images)
    """
    tasks = [detector.detect_async(img) for img in images]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to empty results
    final_results = []
    for result in results:
        if isinstance(result, Exception):
            final_results.append(DetectionResult(
                boxes=np.empty((0, 4), dtype=np.float32),
                scores=np.empty((0,), dtype=np.float32),
                classes=np.empty((0,), dtype=np.int32),
                metadata={'num_detections': 0, 'error': str(result)}
            ))
        else:
            final_results.append(result)

    return final_results
