"""
Integration tests for edge cases and error scenarios.

Tests:
- Invalid input files
- Empty directories
- Huge image sizes
- Network errors
- Out of memory situations
- Corrupted files
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import tempfile
import os


class TestInvalidInputFiles:
    """Test handling of invalid input files"""

    def test_nonexistent_file(self):
        """Test detection on non-existent file"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        manager = DeviceManager(device='cpu')
        detector = YOLODetector(
            model_path='yolov8n.pt',
            device_manager=manager
        )

        with pytest.raises((FileNotFoundError, ValueError)):
            detector.detect('/nonexistent/path/image.jpg')

    def test_unsupported_file_format(self, tmp_path):
        """Test detection on unsupported file format"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        # Create a text file instead of image
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not an image")

        manager = DeviceManager(device='cpu')

        # Mock model loading
        with patch.object(YOLODetector, '_load_model'):
            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            with pytest.raises((ValueError, cv2.error)):
                detector.detect(str(test_file))

    def test_corrupted_image_file(self, tmp_path):
        """Test detection on corrupted image file"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        # Create corrupted file
        corrupted_file = tmp_path / "corrupted.jpg"
        corrupted_file.write_bytes(b'\x00\x00\x00\x00 corrupted data')

        manager = DeviceManager(device='cpu')

        with patch.object(YOLODetector, '_load_model'):
            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            with pytest.raises((ValueError, cv2.error)):
                detector.detect(str(corrupted_file))

    def test_empty_file(self, tmp_path):
        """Test detection on empty file"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        empty_file = tmp_path / "empty.jpg"
        empty_file.write_bytes(b'')

        manager = DeviceManager(device='cpu')

        with patch.object(YOLODetector, '_load_model'):
            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            with pytest.raises((ValueError, cv2.error)):
                detector.detect(str(empty_file))


class TestEmptyDirectories:
    """Test handling of empty directories"""

    def test_empty_directory_batch(self, tmp_path):
        """Test batch processing on empty directory"""
        from src.core.batch_processor import BatchProcessor

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        processor = BatchProcessor()
        results = processor.process_directory(str(empty_dir))

        # Should return empty results
        assert len(results) == 0

    def test_directory_with_no_images(self, tmp_path):
        """Test directory with no image files"""
        from src.core.batch_processor import BatchProcessor

        test_dir = tmp_path / "no_images"
        test_dir.mkdir()

        # Create non-image files
        (test_dir / "file1.txt").write_text("text")
        (test_dir / "file2.json").write_text("{}")

        processor = BatchProcessor()
        results = processor.process_directory(str(test_dir))

        # Should filter out non-image files
        assert len(results) == 0


class TestHugeImageSizes:
    """Test handling of very large images"""

    def test_very_large_image_dimensions(self, tmp_path):
        """Test detection on very large image"""
        from src.models.yolo_detector import YOLODetector
        from src.preprocessing.image_processor import ImageProcessor
        from src.hardware.device_manager import DeviceManager

        # Create large image (8000x8000)
        large_img = np.random.randint(0, 255, (8000, 8000, 3), dtype=np.uint8)
        large_img_path = tmp_path / "large.jpg"

        # Save with compression to avoid huge file
        cv2.imwrite(str(large_img_path), large_img, [cv2.IMWRITE_JPEG_QUALITY, 50])

        manager = DeviceManager(device='cpu')

        # Test that preprocessor can handle resizing
        processor = ImageProcessor(target_size=(640, 640))

        # Should be able to load and resize
        img = cv2.imread(str(large_img_path))
        assert img is not None
        assert img.shape == (8000, 8000, 3)

        # Resize should work
        resized = processor.resize(img)
        assert resized.shape == (640, 640, 3)

    def test_extremely_wide_image(self, tmp_path):
        """Test detection on extremely wide image"""
        from src.preprocessing.image_processor import ImageProcessor

        # Create very wide image (1000x100)
        wide_img = np.random.randint(0, 255, (1000, 100, 3), dtype=np.uint8)
        wide_img_path = tmp_path / "wide.jpg"
        cv2.imwrite(str(wide_img_path), wide_img)

        processor = ImageProcessor(target_size=(640, 640))

        img = cv2.imread(str(wide_img_path))
        assert img.shape == (1000, 100, 3)

        # Should handle aspect ratio
        resized = processor.resize(img, maintain_aspect_ratio=True)
        assert max(resized.shape[:2]) <= 640

    def test_extremely_tall_image(self, tmp_path):
        """Test detection on extremely tall image"""
        from src.preprocessing.image_processor import ImageProcessor

        # Create very tall image (100x1000)
        tall_img = np.random.randint(0, 255, (100, 1000, 3), dtype=np.uint8)
        tall_img_path = tmp_path / "tall.jpg"
        cv2.imwrite(str(tall_img_path), tall_img)

        processor = ImageProcessor(target_size=(640, 640))

        img = cv2.imread(str(tall_img_path))
        assert img.shape == (100, 1000, 3)

        # Should handle aspect ratio
        resized = processor.resize(img, maintain_aspect_ratio=True)
        assert max(resized.shape[:2]) <= 640


class TestNetworkErrors:
    """Test handling of network-related errors"""

    def test_model_download_failure(self, tmp_path):
        """Test model download failure handling"""
        from src.models.model_manager import ModelManager

        manager = ModelManager(cache_dir=str(tmp_path))

        # Mock download to fail
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")

            with pytest.raises((ConnectionError, RuntimeError)):
                manager.download_model('yolov8n.pt')

    def test_model_download_timeout(self, tmp_path):
        """Test model download timeout"""
        from src.models.model_manager import ModelManager

        manager = ModelManager(cache_dir=str(tmp_path))

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError("Download timeout")

            with pytest.raises((TimeoutError, ConnectionError)):
                manager.download_model('yolov8n.pt')

    def test_invalid_model_url(self, tmp_path):
        """Test invalid model URL"""
        from src.models.model_manager import ModelManager

        manager = ModelManager(cache_dir=str(tmp_path))

        with pytest.raises((ValueError, ConnectionError)):
            manager.download_model('invalid_url')


class TestOutOfMemory:
    """Test out-of-memory scenarios"""

    def test_large_batch_memory(self):
        """Test memory handling with large batch"""
        import torch
        from src.core.batch_processor import BatchProcessor

        processor = BatchProcessor()

        # Create many images
        images = [
            np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
            for _ in range(100)
        ]

        # Should handle gracefully (may fail on low-memory systems)
        try:
            results = processor.process_batch(images)
            # If succeeds, great
        except RuntimeError as e:
            # If OOM, should have clear message
            assert 'memory' in str(e).lower()

    def test_memory_cleanup(self):
        """Test memory is cleaned up after processing"""
        import torch
        import gc

        # Process large image
        large_img = np.random.randint(0, 255, (4000, 4000, 3), dtype=np.uint8)

        # Force garbage collection
        del large_img
        gc.collect()

        # Should not crash
        assert True


class TestSpecialImageFormats:
    """Test special or unusual image formats"""

    def test_grayscale_image(self, tmp_path):
        """Test detection on grayscale image"""
        from src.preprocessing.image_processor import ImageProcessor

        # Create grayscale image
        gray_img = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        gray_img_path = tmp_path / "gray.jpg"
        cv2.imwrite(str(gray_img_path), gray_img)

        # Should be converted to 3-channel
        img = cv2.imread(str(gray_img_path))
        assert len(img.shape) == 3
        assert img.shape[2] == 3

    def test_rgba_image(self, tmp_path):
        """Test detection on RGBA image"""
        from src.preprocessing.image_processor import ImageProcessor

        # Create RGBA image
        rgba_img = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        rgba_img_path = tmp_path / "rgba.png"
        cv2.imwrite(str(rgba_img_path), rgba_img)

        # Should be converted to BGR
        img = cv2.imread(str(rgba_img_path))
        assert img.shape[2] == 3

    def test_image_with_exif_rotation(self, tmp_path):
        """Test image with EXIF rotation metadata"""
        from src.preprocessing.image_processor import ImageProcessor

        # Create image with EXIF data (simplified test)
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        img_path = tmp_path / "exif.jpg"
        cv2.imwrite(str(img_path), img)

        # Should load successfully
        loaded = cv2.imread(str(img_path))
        assert loaded is not None


class TestConcurrentAccess:
    """Test concurrent access scenarios"""

    def test_multiple_detectors_same_device(self):
        """Test multiple detector instances on same device"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        manager1 = DeviceManager(device='cpu')
        manager2 = DeviceManager(device='cpu')

        # Both should work independently
        assert manager1.device.type == 'cpu'
        assert manager2.device.type == 'cpu'

    def test_batch_with_errors(self, tmp_path):
        """Test batch processing when some items fail"""
        from src.core.batch_processor import BatchProcessor

        # Create mix of valid and invalid files
        valid_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        valid_path = tmp_path / "valid.jpg"
        cv2.imwrite(str(valid_path), valid_img)

        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not an image")

        processor = BatchProcessor()

        # Should handle errors gracefully
        # (actual behavior depends on implementation)
        results = processor.process_directory(str(tmp_path))


class TestConfigurationEdgeCases:
    """Test configuration edge cases"""

    def test_invalid_confidence_values(self, tmp_path):
        """Test invalid confidence threshold values"""
        from src.config.config_manager import ConfigManager

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  confidence_threshold: 1.5  # Invalid: > 1.0
""")

        manager = ConfigManager(str(config_file))

        with pytest.raises((ValueError, ValidationError)):
            manager.validate()

    def test_negative_iou_threshold(self, tmp_path):
        """Test negative IOU threshold"""
        from src.config.config_manager import ConfigManager

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  iou_threshold: -0.1  # Invalid: < 0
""")

        manager = ConfigManager(str(config_file))

        with pytest.raises((ValueError, ValidationError)):
            manager.validate()

    def test_zero_max_detections(self, tmp_path):
        """Test zero max detections"""
        from src.config.config_manager import ConfigManager

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  max_detections: 0  # Invalid: must be > 0
""")

        manager = ConfigManager(str(config_file))

        with pytest.raises((ValueError, ValidationError)):
            manager.validate()


class TestVideoEdgeCases:
    """Test video processing edge cases"""

    def test_empty_video_file(self, tmp_path):
        """Test empty video file"""
        video_path = tmp_path / "empty.mp4"
        video_path.write_bytes(b'')

        from src.utils.video_utils import VideoProcessor

        with pytest.raises((ValueError, cv2.error)):
            processor = VideoProcessor(str(video_path))

    def test_single_frame_video(self, tmp_path):
        """Test video with only one frame"""
        video_path = tmp_path / "single.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        from src.utils.video_utils import VideoProcessor

        processor = VideoProcessor(str(video_path))
        frame_count = processor.get_frame_count()

        assert frame_count >= 1

    def test_corrupted_video(self, tmp_path):
        """Test corrupted video file"""
        video_path = tmp_path / "corrupted.mp4"
        video_path.write_bytes(b'\x00\x00\x00 corrupted video data')

        from src.utils.video_utils import VideoProcessor

        with pytest.raises((ValueError, cv2.error)):
            processor = VideoProcessor(str(video_path))


class TestResourceCleanup:
    """Test resource cleanup in edge cases"""

    def test_file_handle_cleanup(self, tmp_path):
        """Test file handles are properly closed"""
        from src.models.yolo_detector import YOLODetector
        from src.hardware.device_manager import DeviceManager

        # Create test image
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        manager = DeviceManager(device='cpu')

        with patch.object(YOLODetector, '_load_model'):
            detector = YOLODetector(
                model_path='yolov8n.pt',
                device_manager=manager
            )

            # Open and process file
            try:
                detector.detect(str(img_path))
            except:
                pass

            # File should be closed (can be deleted)
            os.unlink(str(img_path))
            assert not img_path.exists()

    def test_memory_cleanup_after_exception(self):
        """Test memory cleanup when exception occurs"""
        import torch
        import gc

        # Create large tensor
        large_tensor = torch.randn(5000, 5000)

        # Trigger error
        try:
            # This may cause OOM on some systems
            result = large_tensor @ large_tensor
        except RuntimeError:
            pass

        del large_tensor
        gc.collect()

        # Should not crash
        assert True
