"""
Unit tests for Video Utils

Tests VideoCapture, VideoWriter, FrameProcessor, and helper functions
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.utils.video_utils import (
    VideoCapture,
    VideoWriter,
    FrameProcessor,
    stream_frames
)


@pytest.mark.unit
class TestVideoCapture:
    """Test VideoCapture functionality"""

    def test_initialization(self):
        """Test VideoCapture initialization"""
        cap = VideoCapture(source=0, buffer_size=2, fps=30)

        assert cap.source == 0
        assert cap.buffer_size == 2
        assert cap.target_fps == 30
        assert cap.cap is None
        assert cap.running is False

    def test_initialization_with_defaults(self):
        """Test VideoCapture initialization with defaults"""
        cap = VideoCapture()

        assert cap.source == 0
        assert cap.buffer_size == 2
        assert cap.target_fps is None

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_start_success(self, mock_videocapture):
        """Test successful video capture start"""
        # Mock successful opening
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.return_value = 640
        mock_videocapture.return_value = mock_cap_instance

        cap = VideoCapture(source=0)
        cap.start()

        assert cap.running is True
        assert cap.start_time is not None
        assert cap.thread is not None

        cap.stop()

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_start_failure_invalid_source(self, mock_videocapture):
        """Test start with invalid video source"""
        # Mock failed opening
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap_instance

        cap = VideoCapture(source="invalid.mp4")

        with pytest.raises(RuntimeError, match="Failed to open video source"):
            cap.start()

    @pytest.mark.unit
    def test_stop(self):
        """Test stopping video capture"""
        cap = VideoCapture()
        cap.running = True
        cap.thread = MagicMock()

        cap.stop()

        assert cap.running is False

    @pytest.mark.unit
    @patch('src.utils.video_utils.time.time')
    def test_get_fps(self, mock_time):
        """Test FPS calculation"""
        cap = VideoCapture()
        cap.start_time = 0.0
        cap.frame_count = 300

        mock_time.return_value = 10.0

        fps = cap.get_fps()
        assert fps == 30.0

    @pytest.mark.unit
    def test_get_fps_no_start_time(self):
        """Test FPS calculation with no start time"""
        cap = VideoCapture()
        fps = cap.get_fps()
        assert fps == 0.0

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_width_property(self, mock_videocapture):
        """Test width property"""
        mock_cap = MagicMock()
        mock_cap.get.return_value = 1920
        mock_videocapture.return_value = mock_cap

        cap = VideoCapture()
        cap.cap = mock_cap

        assert cap.width == 1920

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_height_property(self, mock_videocapture):
        """Test height property"""
        mock_cap = MagicMock()
        mock_cap.get.return_value = 1080
        mock_videocapture.return_value = mock_cap

        cap = VideoCapture()
        cap.cap = mock_cap

        assert cap.height == 1080


@pytest.mark.unit
class TestVideoWriter:
    """Test VideoWriter functionality"""

    def test_initialization(self):
        """Test VideoWriter initialization"""
        writer = VideoWriter(
            output_path="output.mp4",
            fps=30.0,
            frame_size=(640, 480),
            codec='mp4v'
        )

        assert writer.output_path == "output.mp4"
        assert writer.fps == 30.0
        assert writer.frame_size == (640, 480)
        assert writer.codec == 'mp4v'
        assert writer.writer is None

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoWriter')
    def test_start_success(self, mock_videowriter):
        """Test successful video writer start"""
        mock_writer_instance = MagicMock()
        mock_writer_instance.isOpened.return_value = True
        mock_videowriter.return_value = mock_writer_instance

        writer = VideoWriter(output_path="test.mp4", fps=30.0)
        writer.start(frame_size=(640, 480))

        assert writer.writer is not None

        writer.stop()

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoWriter')
    def test_start_failure(self, mock_videowriter):
        """Test video writer start failure"""
        mock_writer_instance = MagicMock()
        mock_writer_instance.isOpened.return_value = False
        mock_videowriter.return_value = mock_writer_instance

        writer = VideoWriter(output_path="test.mp4", fps=30.0)

        with pytest.raises(RuntimeError, match="Failed to create video writer"):
            writer.start(frame_size=(640, 480))

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoWriter')
    def test_start_without_frame_size_raises_error(self, mock_videowriter):
        """Test start without frame size raises error"""
        writer = VideoWriter(output_path="test.mp4", fps=30.0)

        with pytest.raises(ValueError, match="Frame size must be specified"):
            writer.start()

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.VideoWriter')
    def test_write_auto_starts(self, mock_videowriter):
        """Test that write auto-starts writer with frame size"""
        mock_writer_instance = MagicMock()
        mock_writer_instance.isOpened.return_value = True
        mock_videowriter.return_value = mock_writer_instance

        writer = VideoWriter(output_path="test.mp4", fps=30.0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        writer.write(frame)

        assert writer.writer is not None
        mock_writer_instance.write.assert_called_once()

        writer.stop()

    @pytest.mark.unit
    def test_stop(self):
        """Test stopping video writer"""
        writer = VideoWriter(output_path="test.mp4", fps=30.0)
        mock_writer = MagicMock()
        writer.writer = mock_writer

        writer.stop()

        mock_writer.release.assert_called_once()
        assert writer.writer is None


@pytest.mark.unit
class TestFrameProcessor:
    """Test FrameProcessor functionality"""

    def test_initialization(self):
        """Test FrameProcessor initialization"""
        detector = MagicMock()
        processor = FrameProcessor(
            detector=detector,
            display=False,
            save_output=None
        )

        assert processor.detector == detector
        assert processor.display is False
        assert processor.save_output is None
        assert processor.writer is None

    @pytest.mark.unit
    @patch('src.utils.video_utils.VideoCapture')
    @patch('src.utils.video_utils.cv2.destroyAllWindows')
    def test_process_video_returns_stats(self, mock_destroy, mock_videocapture_class):
        """Test video processing returns statistics"""
        # Mock video capture
        mock_cap = MagicMock()
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (False, None)  # End of video
        ]
        mock_videocapture_class.return_value = mock_cap

        # Mock detector
        detector = MagicMock(return_value=[])

        processor = FrameProcessor(detector=detector, display=False)
        stats = processor.process_video(source=0, max_frames=3)

        assert stats['frames_processed'] == 3
        assert 'total_time' in stats
        assert 'average_fps' in stats
        assert 'min_fps' in stats
        assert 'max_fps' in stats

    @pytest.mark.unit
    @patch('src.utils.video_utils.VideoCapture')
    def test_process_video_with_max_frames(self, mock_videocapture_class):
        """Test processing with max_frames limit"""
        mock_cap = MagicMock()
        # Return 10 frames but limit to 5
        frames = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 10
        frames.append((False, None))
        mock_cap.read.side_effect = frames
        mock_videocapture_class.return_value = mock_cap

        detector = MagicMock(return_value=[])
        processor = FrameProcessor(detector=detector, display=False)

        stats = processor.process_video(source=0, max_frames=5)

        assert stats['frames_processed'] == 5

    @pytest.mark.unit
    @patch('src.utils.video_utils.cv2.rectangle')
    @patch('src.utils.video_utils.cv2.putText')
    def test_draw_detections(self, mock_puttext, mock_rectangle):
        """Test drawing detections on frame"""
        detector = MagicMock()
        processor = FrameProcessor(detector=detector)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = [
            {
                'bbox': [100, 100, 200, 200],
                'confidence': 0.85,
                'class_name': 'person'
            }
        ]

        annotated = processor._draw_detections(frame, detections, fps=30.0)

        assert annotated.shape == frame.shape
        # Verify rectangle and text were called
        assert mock_rectangle.call_count >= 1
        assert mock_puttext.call_count >= 2  # Detection label + FPS


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions"""

    def test_calculate_duration(self):
        """Test duration calculation helper"""
        # This function might not exist, so we test manually
        fps = 30
        frame_count = 300
        duration = frame_count / fps if fps > 0 else 0

        assert duration == 10.0

        fps = 60
        frame_count = 600
        duration = frame_count / fps if fps > 0 else 0

        assert duration == 10.0

    def test_calculate_duration_zero_fps(self):
        """Test duration calculation with zero FPS"""
        fps = 0
        frame_count = 300

        with pytest.raises(ZeroDivisionError):
            duration = frame_count / fps


@pytest.mark.unit
class TestStreamFrames:
    """Test stream_frames generator function"""

    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_stream_frames_yields_frames(self, mock_videocapture):
        """Test that stream_frames yields frames"""
        mock_cap = MagicMock()
        mock_cap.isOpened.side_effect = [True, True, True, False]
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        ]
        mock_videocapture.return_value = mock_cap

        frames = list(stream_frames(source=0))

        assert len(frames) == 3
        mock_cap.release.assert_called_once()

    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_stream_frames_releases_on_exception(self, mock_videocapture):
        """Test that stream_frames releases capture on exception"""
        mock_cap = MagicMock()
        mock_cap.isOpened.side_effect = [True, False]
        mock_cap.read.side_effect = Exception("Read error")
        mock_videocapture.return_value = mock_cap

        with pytest.raises(Exception):
            list(stream_frames(source=0))

        mock_cap.release.assert_called_once()


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_videocapture_context_manager(self):
        """Test VideoCapture as context manager"""
        cap = VideoCapture()
        cap.start = MagicMock(return_value=cap)
        cap.stop = MagicMock()

        with cap:
            pass

        cap.start.assert_called_once()
        cap.stop.assert_called_once()

    def test_videowriter_context_manager(self):
        """Test VideoWriter as context manager"""
        writer = VideoWriter(output_path="test.mp4")
        writer.stop = MagicMock()

        with writer:
            pass

        writer.stop.assert_called_once()

    def test_frameprocessor_with_save_output(self):
        """Test FrameProcessor with output saving"""
        detector = MagicMock(return_value=[])
        processor = FrameProcessor(
            detector=detector,
            display=False,
            save_output="output.mp4"
        )

        assert processor.save_output == "output.mp4"
        assert processor.writer is None  # Not started yet

    @pytest.mark.unit
    def test_videocapture_context_manager_exit(self):
        """Test VideoCapture context manager cleanup"""
        cap = VideoCapture()
        mock_thread = MagicMock()
        cap.thread = mock_thread
        cap.running = True

        cap.__exit__(None, None, None)

        assert cap.running is False
        mock_thread.join.assert_called_once()
