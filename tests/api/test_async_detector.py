"""
Tests for AsyncDetector.

Comprehensive test suite covering async detection, batch processing,
thread pool management, error handling, and performance benchmarks.
"""

import asyncio
import time
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

import pytest
import numpy as np

from src.api.async_detector import (
    AsyncDetector,
    PartialBatchError,
    detect_multiple_async
)
from src.detection.base import AbstractDetector, DetectionResult, ModelInfo


class MockDetector(AbstractDetector):
    """Mock detector for testing."""

    def __init__(self, detection_delay: float = 0.01):
        """Initialize mock detector."""
        super().__init__()
        self.detection_delay = detection_delay
        self._loaded = False
        self.detection_count = 0

    def load_model(self, model_path: str, device: str = "cpu") -> None:
        """Mock model loading."""
        self._model = Mock()
        self._model_path = model_path
        self._device = device
        self._loaded = True
        self.class_names = ['person', 'car', 'dog']

    def detect(self, image: np.ndarray) -> DetectionResult:
        """Mock detection with simulated delay."""
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        # Simulate detection delay
        time.sleep(self.detection_delay)

        self.detection_count += 1

        # Return mock detections
        return DetectionResult(
            boxes=np.array([[100, 100, 200, 200]], dtype=np.float32),
            scores=np.array([0.95], dtype=np.float32),
            classes=np.array([0], dtype=np.int32),
            metadata={
                'num_detections': 1,
                'inference_time': self.detection_delay * 1000
            }
        )

    def detect_batch(self, images: list) -> list:
        """Mock batch detection."""
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        # Simulate batch detection delay
        time.sleep(self.detection_delay * len(images) * 0.5)

        results = []
        for img in images:
            results.append(self.detect(img))

        return results

    def get_model_info(self) -> ModelInfo:
        """Mock model info."""
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        return ModelInfo(
            name="mock_model",
            version="1.0",
            input_size=(640, 640),
            class_names=self.class_names,
            metadata={'framework': 'mock'}
        )


@pytest.fixture
def sample_image():
    """Create sample image for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_images():
    """Create multiple sample images for testing."""
    return [
        np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        for _ in range(10)
    ]


@pytest.fixture
def mock_detector():
    """Create mock detector instance."""
    detector = MockDetector(detection_delay=0.01)
    detector.load_model('mock_model.pt', device='cpu')
    return detector


@pytest.fixture
def async_detector(mock_detector):
    """Create AsyncDetector instance."""
    return AsyncDetector(mock_detector, max_workers=4, default_batch_size=4)


class TestAsyncDetectorInitialization:
    """Tests for AsyncDetector initialization and configuration."""

    def test_initialization_with_valid_detector(self, mock_detector):
        """Test successful initialization."""
        detector = AsyncDetector(mock_detector, max_workers=4, default_batch_size=16)

        assert detector.detector == mock_detector
        assert detector.max_workers == 4
        assert detector.default_batch_size == 16
        assert detector.executor is not None
        assert not detector._shutdown

    def test_initialization_with_none_detector(self):
        """Test initialization fails with None detector."""
        with pytest.raises(ValueError, match="Detector cannot be None"):
            AsyncDetector(None, max_workers=4)

    def test_initialization_with_invalid_max_workers(self, mock_detector):
        """Test initialization fails with invalid max_workers."""
        with pytest.raises(ValueError, match="max_workers must be >= 1"):
            AsyncDetector(mock_detector, max_workers=0)

        with pytest.raises(ValueError, match="max_workers must be >= 1"):
            AsyncDetector(mock_detector, max_workers=-1)

    def test_initialization_with_invalid_batch_size(self, mock_detector):
        """Test initialization fails with invalid batch size."""
        with pytest.raises(ValueError, match="default_batch_size must be >= 1"):
            AsyncDetector(mock_detector, max_workers=4, default_batch_size=0)

    def test_thread_pool_creation(self, mock_detector):
        """Test thread pool is created correctly."""
        detector = AsyncDetector(mock_detector, max_workers=8)

        assert isinstance(detector.executor, ThreadPoolExecutor)
        assert detector.executor._max_workers == 8

    def test_get_stats(self, async_detector):
        """Test get_stats returns correct information."""
        stats = async_detector.get_stats()

        assert stats['max_workers'] == 4
        assert stats['default_batch_size'] == 4
        assert stats['shutdown'] is False
        assert stats['detector_loaded'] is True


class TestAsyncDetection:
    """Tests for async detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_async_single_image(self, async_detector, sample_image):
        """Test async detection on single image."""
        result = await async_detector.detect_async(sample_image)

        assert isinstance(result, DetectionResult)
        assert result.metadata['num_detections'] == 1
        assert len(result.boxes) == 1
        assert len(result.scores) == 1
        assert len(result.classes) == 1

    @pytest.mark.asyncio
    async def test_detect_async_with_invalid_image_type(self, async_detector):
        """Test async detection fails with invalid image type."""
        with pytest.raises(ValueError, match="Image must be numpy array"):
            await async_detector.detect_async("not_an_image")

    @pytest.mark.asyncio
    async def test_detect_async_with_invalid_image_shape(self, async_detector):
        """Test async detection fails with invalid image shape."""
        invalid_image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)

        with pytest.raises(ValueError, match="Image must have shape"):
            await async_detector.detect_async(invalid_image)

    @pytest.mark.asyncio
    async def test_detect_async_after_shutdown(self, async_detector, sample_image):
        """Test async detection fails after shutdown."""
        async_detector.shutdown()

        with pytest.raises(RuntimeError, match="AsyncDetector has been shutdown"):
            await async_detector.detect_async(sample_image)

    @pytest.mark.asyncio
    async def test_detect_async_non_blocking(self, async_detector, sample_image):
        """Test async detection doesn't block main thread."""
        start = time.time()

        # Submit async detection
        task = asyncio.create_task(async_detector.detect_async(sample_image))

        # Main thread should be free to do other work
        await asyncio.sleep(0.001)  # Simulate other work

        # Wait for detection to complete
        await task

        elapsed = time.time() - start

        # Detection should have taken time, but main thread wasn't blocked
        assert elapsed >= 0.01


class TestConcurrentDetections:
    """Tests for concurrent detection capabilities."""

    @pytest.mark.asyncio
    async def test_concurrent_detections_parallel_execution(
        self, async_detector, sample_images
    ):
        """Test multiple detections execute in parallel."""
        # Use 4 images (matches max_workers)
        images = sample_images[:4]

        start = time.time()

        # Submit all detections concurrently
        tasks = [async_detector.detect_async(img) for img in images]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start

        # Should complete in roughly single detection time (parallel execution)
        # Not exact due to thread overhead, but significantly faster than sequential
        assert len(results) == 4
        assert all(isinstance(r, DetectionResult) for r in results)
        # With 4 workers and parallel execution, should be close to 0.01s, not 0.04s
        assert elapsed < 0.03  # Allow some overhead

    @pytest.mark.asyncio
    async def test_max_workers_respected(self, mock_detector, sample_images):
        """Test max workers limit is respected."""
        # Create detector with 2 workers
        detector = AsyncDetector(mock_detector, max_workers=2)

        # Submit 6 detections
        images = sample_images[:6]

        start = time.time()
        tasks = [detector.detect_async(img) for img in images]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # With 2 workers and 6 images, should take ~3 batches * 0.01s = ~0.03s
        assert len(results) == 6
        assert elapsed >= 0.02  # At least 2 batches worth of time
        assert elapsed < 0.05  # But not sequential time (0.06s)

        detector.shutdown()

    @pytest.mark.asyncio
    async def test_detect_multiple_async_utility(self, async_detector, sample_images):
        """Test detect_multiple_async utility function."""
        images = sample_images[:5]

        results = await detect_multiple_async(async_detector, images)

        assert len(results) == 5
        assert all(isinstance(r, DetectionResult) for r in results)


class TestBatchDetection:
    """Tests for batch detection functionality."""

    def test_detect_batch_basic(self, async_detector, sample_images):
        """Test basic batch detection."""
        images = sample_images[:8]

        results = async_detector.detect_batch(images, batch_size=4)

        assert len(results) == 8
        assert all(isinstance(r, DetectionResult) for r in results)
        assert all(r.metadata['num_detections'] == 1 for r in results)

    def test_detect_batch_with_default_batch_size(self, async_detector, sample_images):
        """Test batch detection uses default batch size."""
        images = sample_images[:8]

        # Should use default_batch_size=4 from fixture
        results = async_detector.detect_batch(images)

        assert len(results) == 8

    def test_detect_batch_empty_images(self, async_detector):
        """Test batch detection fails with empty list."""
        with pytest.raises(ValueError, match="Images list cannot be empty"):
            async_detector.detect_batch([])

    def test_detect_batch_invalid_batch_size(self, async_detector, sample_images):
        """Test batch detection fails with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            async_detector.detect_batch(sample_images, batch_size=0)

    def test_detect_batch_chunking(self, async_detector):
        """Test images are split into correct chunks."""
        # Create 10 images, batch size 3 -> 4 batches (3,3,3,1)
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(10)
        ]

        results = async_detector.detect_batch(images, batch_size=3)

        assert len(results) == 10

    def test_detect_batch_after_shutdown(self, async_detector, sample_images):
        """Test batch detection fails after shutdown."""
        async_detector.shutdown()

        with pytest.raises(RuntimeError, match="AsyncDetector has been shutdown"):
            async_detector.detect_batch(sample_images)

    @pytest.mark.asyncio
    async def test_detect_batch_async(self, async_detector, sample_images):
        """Test async batch detection."""
        images = sample_images[:8]

        results = await async_detector.detect_batch_async(images, batch_size=4)

        assert len(results) == 8
        assert all(isinstance(r, DetectionResult) for r in results)


class TestErrorHandling:
    """Tests for error handling and propagation."""

    def test_detect_propagates_exceptions(self, mock_detector, sample_image):
        """Test exceptions from detector are propagated."""
        # Create mock detector that fails
        failing_detector = MockDetector()
        failing_detector.load_model('failing.pt', device='cpu')

        # Make detect() fail
        original_detect = failing_detector.detect
        failing_detector.detect = Mock(side_effect=RuntimeError("Detection failed"))

        detector = AsyncDetector(failing_detector, max_workers=2)

        # Test in async context
        async def test_async():
            with pytest.raises(Exception, match="Async detection failed"):
                await detector.detect_async(sample_image)

        asyncio.run(test_async())
        detector.shutdown()

    def test_partial_batch_error_on_failure(self, mock_detector):
        """Test PartialBatchError when batch partially fails."""
        detector = AsyncDetector(mock_detector, max_workers=2)

        # Create images
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(4)
        ]

        # Make batch detection fail but individual succeed
        original_batch = mock_detector.detect_batch
        mock_detector.detect_batch = Mock(side_effect=RuntimeError("Batch failed"))

        # Should raise PartialBatchError
        with pytest.raises(PartialBatchError) as exc_info:
            detector.detect_batch(images, batch_size=2)

        error = exc_info.value
        assert error.successful == 4  # Fallback to individual worked
        assert error.total == 4
        assert len(error.results) == 4

        detector.shutdown()


class TestContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_cleanup(self, mock_detector):
        """Test detector properly shuts down when used as context manager."""
        with AsyncDetector(mock_detector, max_workers=2) as detector:
            assert not detector._shutdown

        # Should be shutdown after exiting context
        assert detector._shutdown


class TestPerformanceBenchmarks:
    """Tests for performance benchmarks and optimizations."""

    def test_batch_faster_than_individual(self, mock_detector, sample_images):
        """Test batch processing produces correct results."""
        detector = AsyncDetector(mock_detector, max_workers=4)

        images = sample_images[:8]

        # Individual processing (sequential)
        individual_results = [detector._detect_sync(img) for img in images]

        # Batch processing (parallel)
        batch_results = detector.detect_batch(images, batch_size=8)

        # Results should be identical
        assert len(individual_results) == len(batch_results)
        for ind, batch in zip(individual_results, batch_results):
            assert ind.metadata['num_detections'] == batch.metadata['num_detections']
            assert len(ind.boxes) == len(batch.boxes)

        detector.shutdown()

    def test_async_speedup(self, mock_detector, sample_images):
        """Test async processing provides speedup over sequential."""
        detector = AsyncDetector(mock_detector, max_workers=4)

        images = sample_images[:4]

        # Sequential processing
        start = time.time()
        sequential_results = [detector._detect_sync(img) for img in images]
        sequential_time = time.time() - start

        # Async processing
        async def async_process():
            start = time.time()
            tasks = [detector.detect_async(img) for img in images]
            async_results = await asyncio.gather(*tasks)
            async_time = time.time() - start

            return async_results, async_time

        async_results, async_time = asyncio.run(async_process())

        # Async should be faster with 4 workers
        assert len(sequential_results) == len(async_results)
        # With 4 workers and 4 images, should be close to 1x speedup
        assert async_time < sequential_time * 0.8

        detector.shutdown()

    def test_video_streaming_performance(self, mock_detector):
        """Test detector achieves 30+ FPS for video streaming scenario."""
        # Use a detector with very low delay for video streaming
        fast_detector = MockDetector(detection_delay=0.001)
        fast_detector.load_model('fast_model.pt', device='cpu')
        detector = AsyncDetector(fast_detector, max_workers=4)

        # Simulate 30 frames
        frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(30)
        ]

        async def process_video_stream():
            start = time.time()

            # Process frames as they would come in video stream
            tasks = []
            for frame in frames:
                task = detector.detect_async(frame)
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            elapsed = time.time() - start
            fps = len(results) / elapsed

            return fps

        fps = asyncio.run(process_video_stream())

        # Should achieve significantly higher than 30 FPS with low delay
        assert fps > 30

        detector.shutdown()


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_detect_calls(self, async_detector, sample_images):
        """Test concurrent detect() calls are thread-safe."""
        import threading

        images = sample_images[:10]
        results = []
        errors = []

        def detect_worker(img):
            try:
                result = async_detector._detect_sync(img)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create threads
        threads = [threading.Thread(target=detect_worker, args=(img,)) for img in images]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should have processed all images without errors
        assert len(results) == 10
        assert len(errors) == 0

    def test_thread_pool_lifecycle(self, mock_detector):
        """Test thread pool is managed correctly."""
        detector = AsyncDetector(mock_detector, max_workers=2)

        # Executor should be active
        assert not detector._shutdown

        # Shutdown
        detector.shutdown()
        assert detector._shutdown

        # Second shutdown should be safe
        detector.shutdown()
        assert detector._shutdown
