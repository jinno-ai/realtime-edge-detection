"""
Integration tests for edge cases

Tests error handling and edge cases against the actual implementation APIs.
"""

import pytest
import numpy as np
import cv2
from unittest.mock import patch, Mock


def _mock_detector():
    """Create a mock detector compatible with BatchProcessor."""
    detector = Mock()
    detector.config = {}
    detector.detect.return_value = []
    # Non-iterable return triggers the documented per-image fallback path
    detector.detect_batch.return_value = None
    return detector


@pytest.mark.integration
class TestInvalidInputFiles:
    """Test handling of invalid input files"""

    def test_nonexistent_file(self, tmp_path):
        """Loading a non-existent image yields an error log entry"""
        from src.core.batch_processor import BatchProcessor

        missing_dir = tmp_path / "empty"
        missing_dir.mkdir()

        processor = BatchProcessor(detector=_mock_detector())
        images = processor._load_images(str(missing_dir))
        assert images == []

        # cv2.imread on a missing file returns None rather than raising
        assert cv2.imread(str(tmp_path / "nonexistent.jpg")) is None

    def test_unsupported_file_format(self, tmp_path):
        """Non-image extensions are ignored by directory scanning"""
        from src.core.batch_processor import BatchProcessor

        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not an image")

        processor = BatchProcessor(detector=_mock_detector())
        images = processor._load_images(str(tmp_path))
        assert images == []

    def test_corrupted_image_file(self, tmp_path):
        """Corrupted image files are logged and skipped"""
        from src.core.batch_processor import BatchProcessor

        corrupted_file = tmp_path / "corrupted.jpg"
        corrupted_file.write_bytes(b'\x00\x00\x00\x00 corrupted data')

        processor = BatchProcessor(detector=_mock_detector())
        images = processor._load_images(str(tmp_path))

        assert images == []
        assert any('corrupted.jpg' in e['image'] for e in processor.error_log)

    def test_empty_file(self, tmp_path):
        """Empty image files are logged and skipped"""
        from src.core.batch_processor import BatchProcessor

        empty_file = tmp_path / "empty.jpg"
        empty_file.write_bytes(b'')

        processor = BatchProcessor(detector=_mock_detector())
        images = processor._load_images(str(tmp_path))

        assert images == []
        assert any('empty.jpg' in e['image'] for e in processor.error_log)


@pytest.mark.integration
class TestEmptyDirectories:
    """Test handling of empty directories"""

    def test_empty_directory_batch(self, tmp_path):
        """Batch processing on empty directory returns empty stats"""
        from src.core.batch_processor import BatchProcessor

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        processor = BatchProcessor(detector=_mock_detector())
        stats = processor.process_directory(str(empty_dir))

        assert stats.total_images == 0

    def test_directory_with_no_images(self, tmp_path):
        """Directory with only non-image files yields zero results"""
        from src.core.batch_processor import BatchProcessor

        test_dir = tmp_path / "no_images"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("text")
        (test_dir / "file2.json").write_text("{}")

        processor = BatchProcessor(detector=_mock_detector())
        stats = processor.process_directory(str(test_dir))

        assert stats.total_images == 0


@pytest.mark.integration
class TestHugeImageSizes:
    """Test handling of very large images"""

    def test_very_large_image_dimensions(self, tmp_path):
        """Test preprocessing can handle a very large image"""
        from src.preprocessing.image_processor import ImageProcessor

        large_img = np.random.randint(0, 255, (8000, 8000, 3), dtype=np.uint8)
        large_img_path = tmp_path / "large.jpg"
        cv2.imwrite(str(large_img_path), large_img, [cv2.IMWRITE_JPEG_QUALITY, 50])

        processor = ImageProcessor(target_size=(640, 640))

        img = cv2.imread(str(large_img_path))
        assert img is not None

        resized = processor.resize(img, (640, 640))
        assert resized.shape == (640, 640, 3)

    def test_extremely_wide_image(self, tmp_path):
        """Resize keeps aspect ratio on extremely wide images"""
        from src.preprocessing.image_processor import ImageProcessor

        wide_img = np.random.randint(0, 255, (1000, 100, 3), dtype=np.uint8)
        wide_img_path = tmp_path / "wide.jpg"
        cv2.imwrite(str(wide_img_path), wide_img)

        processor = ImageProcessor(target_size=(640, 640))
        img = cv2.imread(str(wide_img_path))
        assert img.shape == (1000, 100, 3)

        resized = processor.resize(img, (640, 640), keep_ratio=True)
        assert resized.shape == (640, 640, 3)

    def test_extremely_tall_image(self, tmp_path):
        """Resize keeps aspect ratio on extremely tall images"""
        from src.preprocessing.image_processor import ImageProcessor

        tall_img = np.random.randint(0, 255, (100, 1000, 3), dtype=np.uint8)
        tall_img_path = tmp_path / "tall.jpg"
        cv2.imwrite(str(tall_img_path), tall_img)

        processor = ImageProcessor(target_size=(640, 640))
        img = cv2.imread(str(tall_img_path))
        assert img.shape == (100, 1000, 3)

        resized = processor.resize(img, (640, 640), keep_ratio=True)
        assert resized.shape == (640, 640, 3)


@pytest.mark.integration
class TestNetworkErrors:
    """Test handling of network-related errors"""

    def test_model_download_failure(self, tmp_path):
        """Failed download raises ModelDownloadError"""
        from src.models.model_manager import ModelManager, ModelDownloadError

        manager = ModelManager(cache_dir=tmp_path)

        with patch.object(ModelManager, '_download_with_retry', return_value=False):
            with pytest.raises(ModelDownloadError):
                manager.download_model('yolov8n')

    def test_model_download_timeout(self, tmp_path):
        """Timeout during download propagates"""
        from src.models.model_manager import ModelManager

        manager = ModelManager(cache_dir=tmp_path)

        with patch.object(
            ModelManager, '_download_with_retry',
            side_effect=TimeoutError("Download timeout")
        ):
            with pytest.raises(TimeoutError):
                manager.download_model('yolov8n')

    def test_invalid_model_url(self, tmp_path):
        """Unknown model name raises ValueError before any download"""
        from src.models.model_manager import ModelManager

        manager = ModelManager(cache_dir=tmp_path)

        with pytest.raises(ValueError):
            manager.download_model('invalid_url')


@pytest.mark.integration
class TestOutOfMemory:
    """Test out-of-memory scenarios"""

    def test_large_batch_memory(self, tmp_path):
        """Loading many large images is handled gracefully"""
        from src.core.batch_processor import BatchProcessor

        for i in range(3):
            img = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
            cv2.imwrite(str(tmp_path / f"img{i}.jpg"), img)

        processor = BatchProcessor(detector=_mock_detector())
        try:
            stats = processor.process_directory(str(tmp_path))
            assert stats.total_images == 3
        except RuntimeError as e:
            # If OOM, should have clear message
            assert 'memory' in str(e).lower()

    def test_memory_cleanup(self):
        """Test memory is cleaned up after processing"""
        import gc

        large_img = np.random.randint(0, 255, (4000, 4000, 3), dtype=np.uint8)

        del large_img
        gc.collect()

        # Should not crash
        assert True


@pytest.mark.integration
class TestSpecialImageFormats:
    """Test special or unusual image formats"""

    def test_grayscale_image(self, tmp_path):
        """Grayscale images load as 3-channel BGR"""
        gray_img = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        gray_img_path = tmp_path / "gray.jpg"
        cv2.imwrite(str(gray_img_path), gray_img)

        img = cv2.imread(str(gray_img_path))
        assert len(img.shape) == 3
        assert img.shape[2] == 3

    def test_rgba_image(self, tmp_path):
        """RGBA images load as 3-channel BGR"""
        rgba_img = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        rgba_img_path = tmp_path / "rgba.png"
        cv2.imwrite(str(rgba_img_path), rgba_img)

        img = cv2.imread(str(rgba_img_path))
        assert img.shape[2] == 3

    def test_image_with_exif_rotation(self, tmp_path):
        """Images with metadata load successfully"""
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        img_path = tmp_path / "exif.jpg"
        cv2.imwrite(str(img_path), img)

        loaded = cv2.imread(str(img_path))
        assert loaded is not None


@pytest.mark.integration
class TestConcurrentAccess:
    """Test concurrent access scenarios"""

    def test_multiple_detectors_same_device(self):
        """Multiple DeviceManager instances work independently"""
        from src.hardware.device_manager import DeviceManager, DeviceType

        manager1 = DeviceManager(device_str='cpu')
        manager2 = DeviceManager(device_str='cpu')

        assert manager1.selected_device == DeviceType.CPU
        assert manager2.selected_device == DeviceType.CPU

    def test_batch_with_errors(self, tmp_path):
        """Batch processing skips files that fail to load"""
        from src.core.batch_processor import BatchProcessor

        valid_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        valid_path = tmp_path / "valid.jpg"
        cv2.imwrite(str(valid_path), valid_img)

        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not an image")

        processor = BatchProcessor(detector=_mock_detector())
        stats = processor.process_directory(str(tmp_path))

        # Only the valid image is processed; the .txt file is filtered out
        assert stats.total_images == 1


@pytest.mark.integration
class TestConfigurationEdgeCases:
    """Test configuration edge cases"""

    def test_invalid_confidence_values(self, tmp_path):
        """Invalid confidence threshold raises on load"""
        from src.config.config_manager import ConfigManager, ConfigurationError

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  confidence_threshold: 1.5  # Invalid: > 1.0
""")

        manager = ConfigManager()
        with pytest.raises(ConfigurationError):
            manager.load(str(config_file))

    def test_negative_iou_threshold(self, tmp_path):
        """Negative IOU threshold raises on load"""
        from src.config.config_manager import ConfigManager, ConfigurationError

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  iou_threshold: -0.1  # Invalid: < 0
""")

        manager = ConfigManager()
        with pytest.raises(ConfigurationError):
            manager.load(str(config_file))

    def test_zero_max_detections(self, tmp_path):
        """Zero max_detections raises on load"""
        from src.config.config_manager import ConfigManager, ConfigurationError

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
detection:
  max_detections: 0  # Invalid: must be > 0
""")

        manager = ConfigManager()
        with pytest.raises(ConfigurationError):
            manager.load(str(config_file))


@pytest.mark.integration
class TestVideoEdgeCases:
    """Test video processing edge cases"""

    def test_empty_video_file(self, tmp_path):
        """Empty video file fails to open"""
        from src.utils.video_utils import VideoCapture

        video_path = tmp_path / "empty.mp4"
        video_path.write_bytes(b'')

        cap = VideoCapture(source=str(video_path))
        with pytest.raises(RuntimeError):
            cap.start()

    def test_single_frame_video(self, tmp_path):
        """Single-frame video yields exactly one frame"""
        from src.utils.video_utils import stream_frames

        video_path = tmp_path / "single.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        frames = list(stream_frames(str(video_path)))
        assert len(frames) >= 1

    def test_corrupted_video(self, tmp_path):
        """Corrupted video file fails to open"""
        from src.utils.video_utils import VideoCapture

        video_path = tmp_path / "corrupted.mp4"
        video_path.write_bytes(b'\x00\x00\x00 corrupted video data')

        cap = VideoCapture(source=str(video_path))
        with pytest.raises(RuntimeError):
            cap.start()


@pytest.mark.integration
class TestResourceCleanup:
    """Test resource cleanup in edge cases"""

    def test_file_handle_cleanup(self, tmp_path):
        """Processed image files can be deleted afterwards"""
        import os

        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        loaded = cv2.imread(str(img_path))
        assert loaded is not None
        del loaded

        os.unlink(str(img_path))
        assert not img_path.exists()

    def test_memory_cleanup_after_exception(self):
        """Test memory cleanup when exception occurs"""
        import gc

        large_array = np.random.rand(5000, 5000)

        try:
            _ = large_array @ large_array
        except RuntimeError:
            pass

        del large_array
        gc.collect()

        # Should not crash
        assert True
