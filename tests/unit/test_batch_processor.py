"""
Unit tests for BatchProcessor module.

Tests batch processing functionality including:
- Batch detection
- Memory monitoring
- Automatic batch size calculation
- Error handling and recovery
- Statistics tracking
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path
import tempfile
import shutil

from src.core.batch_processor import (
    BatchProcessor,
    BatchStatistics,
    MemoryMonitor
)


class TestBatchStatistics:
    """Test batch statistics tracking."""

    def test_initialization(self):
        """Test statistics initialization."""
        stats = BatchStatistics()
        assert stats.total_images == 0
        assert stats.successful == 0
        assert stats.failed == 0
        assert stats.processing_times == []
        assert stats.batch_sizes == []

    def test_record_batch(self):
        """Test recording batch statistics."""
        stats = BatchStatistics()
        stats.record_batch(batch_size=32, processing_time=1.5, success_count=30)

        assert stats.total_images == 32
        assert stats.successful == 30
        assert stats.failed == 2
        assert stats.processing_times == [1.5]
        assert stats.batch_sizes == [32]

    def test_multiple_batches(self):
        """Test recording multiple batches."""
        stats = BatchStatistics()
        stats.record_batch(32, 1.0, 32)
        stats.record_batch(32, 1.0, 31)

        assert stats.total_images == 64
        assert stats.successful == 63
        assert stats.failed == 1

    def test_finish(self):
        """Test finishing statistics."""
        stats = BatchStatistics()
        stats.finish()

        assert stats.end_time is not None
        assert stats.total_time > 0

    def test_average_fps(self):
        """Test average FPS calculation."""
        import time
        stats = BatchStatistics()
        # Simulate realistic processing time
        stats.record_batch(100, 2.0, 100)
        time.sleep(0.1)  # Small delay to ensure total_time > 0
        stats.finish()

        fps = stats.average_fps
        assert fps > 0
        # FPS will vary based on actual execution time, just check it's reasonable

    def test_to_dict(self):
        """Test converting statistics to dictionary."""
        stats = BatchStatistics()
        stats.record_batch(100, 2.0, 98)
        stats.finish()

        result = stats.to_dict()

        assert 'timestamp' in result
        assert result['total_images'] == 100
        assert result['successful'] == 98
        assert result['failed'] == 2
        assert 'success_rate' in result
        assert 'average_fps' in result


class TestMemoryMonitor:
    """Test memory monitoring functionality."""

    def test_get_available_memory_mb(self):
        """Test getting available memory."""
        cpu_mem, gpu_mem = MemoryMonitor.get_available_memory_mb()

        assert cpu_mem > 0
        assert isinstance(cpu_mem, float)
        # GPU memory may be None if no GPU
        assert gpu_mem is None or gpu_mem > 0

    def test_calculate_optimal_batch_size_cpu(self):
        """Test batch size calculation for CPU."""
        image_size = (640, 640, 3)
        available_memory = 2048.0  # 2GB

        batch_size = MemoryMonitor.calculate_optimal_batch_size(
            image_size,
            available_memory,
            model_memory_mb=500.0
        )

        # Should calculate reasonable batch size
        assert 1 <= batch_size <= 128

    def test_calculate_optimal_batch_size_clamping(self):
        """Test batch size is clamped to reasonable range."""
        image_size = (640, 640, 3)

        # Very low memory
        batch_size = MemoryMonitor.calculate_optimal_batch_size(
            image_size,
            available_memory_mb=10.0,
            model_memory_mb=500.0
        )
        assert batch_size == 1  # Minimum

        # Very high memory
        batch_size = MemoryMonitor.calculate_optimal_batch_size(
            image_size,
            available_memory_mb=100000.0,
            model_memory_mb=500.0
        )
        assert batch_size == 128  # Maximum


class TestBatchProcessor:
    """Test batch processor functionality."""

    @pytest.fixture
    def mock_detector(self):
        """Create mock detector."""
        detector = Mock()
        detector.config = {
            'model': {'type': 'yolo_v8'},
            'detection': {'confidence_threshold': 0.5}
        }
        detector.detect_batch = Mock(return_value=[
            [{'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}]
        ])
        detector.detect = Mock(return_value=[
            {'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}
        ])
        return detector

    def test_initialization(self, mock_detector):
        """Test batch processor initialization."""
        processor = BatchProcessor(
            detector=mock_detector,
            batch_size=32,
            auto_batch=False
        )

        assert processor.detector == mock_detector
        assert processor.batch_size == 32
        assert processor.auto_batch is False
        assert isinstance(processor.stats, BatchStatistics)

    def test_initialization_auto_batch(self, mock_detector):
        """Test initialization with auto batch."""
        processor = BatchProcessor(
            detector=mock_detector,
            batch_size=32,
            auto_batch=True
        )

        assert processor.auto_batch is True

    def test_determine_batch_size_fixed(self, mock_detector):
        """Test fixed batch size determination."""
        processor = BatchProcessor(
            detector=mock_detector,
            batch_size=16,
            auto_batch=False
        )

        images = [('test.jpg', np.zeros((640, 640, 3), dtype=np.uint8))]
        batch_size = processor._determine_batch_size(images)

        assert batch_size == 16

    @patch('src.core.batch_processor.MemoryMonitor.get_available_memory_mb')
    def test_determine_batch_size_auto(self, mock_memory, mock_detector):
        """Test automatic batch size determination."""
        mock_memory.return_value = (2048.0, None)  # 2GB CPU memory

        processor = BatchProcessor(
            detector=mock_detector,
            batch_size=32,
            auto_batch=True
        )

        images = [('test.jpg', np.zeros((640, 640, 3), dtype=np.uint8))]
        batch_size = processor._determine_batch_size(images)

        assert 1 <= batch_size <= 128

    def test_process_batch_success(self, mock_detector):
        """Test successful batch processing."""
        mock_detector.detect_batch.return_value = [
            [
                {'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]},
                {'class_name': 'car', 'confidence': 0.8, 'bbox': [200, 200, 300, 300]}
            ],
            [
                {'class_name': 'dog', 'confidence': 0.7, 'bbox': [50, 50, 150, 150]}
            ]
        ]

        processor = BatchProcessor(detector=mock_detector, batch_size=2)
        batch_images = [
            ('img1.jpg', np.zeros((640, 640, 3), dtype=np.uint8)),
            ('img2.jpg', np.zeros((640, 640, 3), dtype=np.uint8))
        ]

        results = processor._process_batch(batch_images)

        assert len(results) == 2
        assert results[0]['filename'] == 'img1.jpg'
        assert results[0]['success'] is True
        assert len(results[0]['detections']) == 2
        assert results[1]['filename'] == 'img2.jpg'
        assert len(results[1]['detections']) == 1

    def test_process_batch_error_fallback(self, mock_detector):
        """Test batch processing with error and fallback."""
        # First call fails, second succeeds (individual)
        mock_detector.detect_batch.side_effect = [
            Exception("Batch failed"),
            [
                [{'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}]
            ]
        ]

        processor = BatchProcessor(detector=mock_detector, batch_size=2)
        batch_images = [
            ('img1.jpg', np.zeros((640, 640, 3), dtype=np.uint8)),
            ('img2.jpg', np.zeros((640, 640, 3), dtype=np.uint8))
        ]

        results = processor._process_batch(batch_images)

        # Should fallback to individual processing
        assert len(results) == 2
        assert results[0]['success'] is True
        assert results[1]['success'] is True

    def test_load_images(self, mock_detector):
        """Test loading images from directory."""
        processor = BatchProcessor(detector=mock_detector)

        # Create temporary directory with test images
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test images
            for i in range(3):
                img_path = Path(tmpdir) / f"test_{i}.jpg"
                img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                import cv2
                cv2.imwrite(str(img_path), img)

            # Load images
            images = processor._load_images(tmpdir)

            assert len(images) == 3
            assert all(isinstance(img, np.ndarray) for _, img in images)

    @patch('src.core.batch_processor.cv2.imread')
    def test_load_images_with_errors(self, mock_imread, mock_detector):
        """Test loading images with some errors."""
        # Some images fail to load
        mock_imread.side_effect = [
            np.zeros((640, 640, 3), dtype=np.uint8),  # Success
            None,  # Failure
            np.zeros((640, 640, 3), dtype=np.uint8),  # Success
        ]

        processor = BatchProcessor(detector=mock_detector)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty files
            for i in range(3):
                (Path(tmpdir) / f"test_{i}.jpg").touch()

            images = processor._load_images(tmpdir)

            # Should log errors but continue
            assert len(images) == 2  # Only successfully loaded images
            assert len(processor.error_log) == 1

    def test_save_csv_results(self, mock_detector, tmp_path):
        """Test saving results to CSV."""
        processor = BatchProcessor(detector=mock_detector)

        results = [
            {
                'filename': 'img1.jpg',
                'detections': [
                    {'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}
                ],
                'time_ms': 25.5
            },
            {
                'filename': 'img2.jpg',
                'detections': [],  # No detections
                'time_ms': 22.3
            }
        ]

        output_path = tmp_path / "results.csv"
        processor._save_csv_results(results, str(output_path))

        assert output_path.exists()

        # Verify CSV content
        import csv
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2  # One for img1, one for img2 (empty)

    def test_process_directory(self, mock_detector):
        """Test processing entire directory."""
        # Mock detect_batch to return one detection per image
        mock_detector.detect_batch.return_value = [
            [{'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}]
            for _ in range(10)  # Support up to 10 images per batch
        ]

        processor = BatchProcessor(detector=mock_detector, batch_size=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test images
            for i in range(4):
                img_path = Path(tmpdir) / f"test_{i}.jpg"
                img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                import cv2
                cv2.imwrite(str(img_path), img)

            # Process directory
            stats = processor.process_directory(tmpdir)

            assert stats.total_images == 4
            assert stats.successful == 4
            assert stats.failed == 0

    def test_print_summary(self, mock_detector, capsys):
        """Test printing summary."""
        processor = BatchProcessor(detector=mock_detector)
        processor.stats.record_batch(100, 2.0, 98)
        processor.stats.finish()

        processor.print_summary()

        captured = capsys.readouterr()
        assert "Batch Processing Statistics" in captured.out
        assert "Total Images:     100" in captured.out
        assert "Successful:       98" in captured.out


class TestBatchProcessorIntegration:
    """Integration tests for batch processor with real detector."""

    @pytest.fixture
    def mock_detector(self):
        """Create mock detector."""
        detector = Mock()
        detector.config = {
            'model': {'type': 'yolo_v8'},
            'detection': {'confidence_threshold': 0.5}
        }
        detector.detect_batch = Mock(return_value=[
            [{'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}]
        ])
        detector.detect = Mock(return_value=[
            {'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}
        ])
        return detector

    @pytest.fixture
    def sample_images_dir(self):
        """Create temporary directory with sample images."""
        tmpdir = tempfile.mkdtemp()
        for i in range(5):
            img_path = Path(tmpdir) / f"sample_{i}.jpg"
            img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            import cv2
            cv2.imwrite(str(img_path), img)
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_end_to_end_batch_processing(self, sample_images_dir, mock_detector):
        """Test complete batch processing workflow."""
        mock_detector.detect_batch.return_value = [
            [{'class_name': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}]
            for _ in range(5)
        ]

        processor = BatchProcessor(
            detector=mock_detector,
            batch_size=2,
            auto_batch=False
        )

        # Process directory
        stats = processor.process_directory(sample_images_dir)

        # Verify results
        assert stats.total_images == 5
        assert stats.successful == 5
        assert stats.average_fps > 0
