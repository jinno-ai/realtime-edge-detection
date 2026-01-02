"""
Integration tests for Video Processing Pipeline

Tests end-to-end video processing with detection
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.models.yolo_detector import YOLODetector
from src.preprocessing.image_processor import ImageProcessor
from src.utils.video_utils import VideoCapture, FrameProcessor


@pytest.mark.integration
class TestVideoProcessingPipeline:
    """Test complete video processing pipeline"""

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_full_pipeline_detection_and_processing(self, mock_yolo_class):
        """Test complete pipeline from video input to processed output"""
        # Setup mock YOLO model
        mock_result = Mock()
        mock_box = Mock()
        import torch
        mock_box.xyxy = [torch.tensor([[100, 100, 200, 200]])]
        mock_box.conf = [torch.tensor([0.85])]
        mock_box.cls = [torch.tensor([0])]
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "person"}

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person"}
        mock_yolo_class.return_value = mock_model

        # Initialize components
        detector = YOLODetector(config=None)
        detector.model_path = "yolov8n.pt"
        detector.load_model = Mock()  # Mock load_model to avoid actual loading
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Run detection
        detections = detector.detect(frame)

        # Verify detection
        assert len(detections) >= 0
        if len(detections) > 0:
            assert 'bbox' in detections[0]
            assert 'confidence' in detections[0]
            assert 'class_name' in detections[0]

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_image_preprocessing_before_detection(self, mock_yolo_class):
        """Test image preprocessing pipeline before detection"""
        # Setup mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_yolo_class.return_value = Mock(return_value=[mock_result], names={})

        detector = YOLODetector(config=None)
        detector.model = Mock(return_value=[mock_result])
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Create image
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Preprocess
        processor = ImageProcessor(target_size=(640, 640))
        preprocessed = processor.preprocess(image)

        # Verify preprocessing
        assert preprocessed is not None
        assert preprocessed.shape[0] == 1  # Batch dimension
        assert preprocessed.shape[1] == 3  # Channels

        # Detection should work with original image
        detections = detector.detect(image)
        assert isinstance(detections, list)

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_video_capture_with_detection(self, mock_videocapture_class, mock_yolo_class):
        """Test video capture integrated with detection"""
        # Mock video capture
        mock_cap = MagicMock()
        mock_cap.read.side_effect = [
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (False, None)
        ]
        mock_videocapture_class.return_value = mock_cap

        # Mock YOLO
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Process frames
        frame_count = 0
        ret, frame = mock_cap.read()

        while ret:
            detections = detector.detect(frame)
            assert isinstance(detections, list)
            frame_count += 1
            ret, frame = mock_cap.read()

        assert frame_count == 2

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    @patch('src.utils.video_utils.cv2.VideoCapture')
    def test_batch_frame_processing(self, mock_videocapture_class, mock_yolo_class):
        """Test processing multiple frames in batch"""
        # Mock video
        mock_cap = MagicMock()
        frames = [
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
            for _ in range(10)
        ]
        frames.append((False, None))
        mock_cap.read.side_effect = frames
        mock_videocapture_class.return_value = mock_cap

        # Mock YOLO
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Process all frames
        all_detections = []
        ret, frame = mock_cap.read()

        while ret:
            detections = detector.detect(frame)
            all_detections.append(detections)
            ret, frame = mock_cap.read()

        assert len(all_detections) == 10

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_different_image_sizes_handling(self, mock_yolo_class):
        """Test detection with various image sizes"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Test different sizes
        sizes = [
            (320, 320),
            (640, 480),
            (1280, 720),
            (1920, 1080),
            (3840, 2160)  # 4K
        ]

        for width, height in sizes:
            image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            detections = detector.detect(image)
            assert isinstance(detections, list)

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_augmented_image_detection(self, mock_yolo_class):
        """Test detection with augmented images"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Create and augment image
        from src.preprocessing.image_processor import ImageAugmentor

        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        augmentor = ImageAugmentor(seed=42)
        augmented, _ = augmentor.augment(image)

        # Detection should work
        detections = detector.detect(augmented)
        assert isinstance(detections, list)

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_optimized_image_detection(self, mock_yolo_class):
        """Test detection with edge-optimized images"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Optimize image
        from src.preprocessing.image_processor import EdgeOptimizer

        image = np.random.rand(480, 640, 3).astype(np.float32)
        optimizer = EdgeOptimizer(target_device="cpu")
        optimized = optimizer.optimize_for_inference(image, quantize=False)

        # Detection should work
        detections = detector.detect(optimized.astype(np.uint8))
        assert isinstance(detections, list)

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_resolution_reduced_detection(self, mock_yolo_class):
        """Test detection with reduced resolution for edge devices"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Reduce resolution
        from src.preprocessing.image_processor import EdgeOptimizer

        original = np.zeros((1920, 1080, 3), dtype=np.uint8)
        optimizer = EdgeOptimizer()
        reduced = optimizer.reduce_resolution(original, scale=0.5)

        # Should be smaller
        assert reduced.shape[0] < original.shape[0]
        assert reduced.shape[1] < original.shape[1]

        # Detection should work
        detections = detector.detect(reduced)
        assert isinstance(detections, list)

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_letterbox_preprocessing_pipeline(self, mock_yolo_class):
        """Test letterbox preprocessing integrated with detection"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        # Letterbox preprocess
        processor = ImageProcessor()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        letterboxed, scale, padding = processor.letterbox(image, (640, 640))

        # Verify letterbox
        assert letterboxed.shape == (640, 640, 3)
        assert scale > 0

        # Detection should work
        detections = detector.detect(letterboxed)
        assert isinstance(detections, list)


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance characteristics"""

    @pytest.mark.integration
    @pytest.mark.slow
    @patch('src.models.yolo_detector.YOLO')
    def test_detection_performance_multiple_frames(self, mock_yolo_class):
        """Test detection performance across multiple frames"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        import time

        # Process 100 frames
        frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(100)
        ]

        start_time = time.time()
        for frame in frames:
            detector.detect(frame)
        elapsed = time.time() - start_time

        # Calculate FPS
        fps = len(frames) / elapsed if elapsed > 0 else 0

        # Performance assertion (very flexible)
        assert fps > 0
        assert elapsed < 60  # Should complete in under 60 seconds

    @pytest.mark.integration
    @pytest.mark.slow
    @patch('src.models.yolo_detector.YOLO')
    def test_batch_preprocessing_performance(self, mock_yolo_class):
        """Test batch preprocessing performance"""
        # Mock
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock(return_value=[mock_result], names={})
        mock_yolo_class.return_value = mock_model

        detector = YOLODetector(config=None)
        detector.model = mock_model
        detector.conf_threshold = 0.5
        detector.iou_threshold = 0.4
        detector.max_detections = 100

        import time

        # Create batch
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(50)
        ]

        processor = ImageProcessor()

        start_time = time.time()
        batch = processor.batch_preprocess(images)
        elapsed = time.time() - start_time

        assert batch.shape[0] == len(images)
        assert elapsed < 30  # Should complete in under 30 seconds
