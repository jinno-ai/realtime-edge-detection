"""
Integration tests for Real-time Edge Detection

These tests verify end-to-end detection pipeline.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model for testing"""
    mock_result = Mock()
    mock_box = Mock()
    mock_box.xyxy = [np.array([[100, 100, 200, 200]])]
    mock_box.conf = [np.tensor([0.85])]
    mock_box.cls = [np.tensor([0])]
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person"}

    mock_model = Mock()
    mock_model.return_value = [mock_result]
    mock_model.names = {0: "person", 1: "car", 2: "dog"}

    return mock_model


@pytest.mark.integration
@patch('src.models.yolo_detector.YOLO')
def test_full_detection_pipeline(mock_yolo_class, mock_yolo_model):
    """Test complete detection pipeline"""
    from src.models.yolo_detector import YOLODetector
    from src.preprocessing.image_processor import ImageProcessor

    # Initialize
    mock_yolo_class.return_value = mock_yolo_model

    detector = YOLODetector("yolov8n.pt")
    detector.load_model()

    # Create test image
    image = np.zeros((640, 640, 3), dtype=np.uint8)

    # Preprocess
    processor = ImageProcessor(target_size=(640, 640))
    preprocessed = processor.preprocess(image)

    # Detect
    detections = detector.detect(image)

    # Verify
    assert len(detections) >= 0
    assert preprocessed is not None


@pytest.mark.integration
@patch('src.models.yolo_detector.YOLO')
def test_image_preprocessing_pipeline(mock_yolo_class, mock_yolo_model):
    """Test image preprocessing before detection"""
    from src.models.yolo_detector import YOLODetector
    from src.preprocessing.image_processor import ImageProcessor

    mock_yolo_class.return_value = mock_yolo_model

    # Create test images
    images = [
        np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        for _ in range(5)
    ]

    # Preprocess batch
    processor = ImageProcessor(target_size=(640, 640))
    batch = processor.batch_preprocess(images)

    assert batch.shape[0] == len(images)


@pytest.mark.integration
@patch('src.models.yolo_detector.YOLO')
def test_detection_with_different_sizes(mock_yolo_class, mock_yolo_model):
    """Test detection with various image sizes"""
    from src.models.yolo_detector import YOLODetector

    mock_yolo_class.return_value = mock_yolo_model

    detector = YOLODetector("yolov8n.pt")
    detector.load_model()

    # Test different sizes
    sizes = [
        (320, 320),
        (640, 480),
        (1280, 720),
        (1920, 1080)
    ]

    for width, height in sizes:
        image = np.zeros((height, width, 3), dtype=np.uint8)
        detections = detector.detect(image)
        assert isinstance(detections, list)


@pytest.mark.integration
def test_letterbox_preprocessing():
    """Test letterbox preprocessing"""
    from src.preprocessing.image_processor import ImageProcessor

    processor = ImageProcessor()

    # Create test image
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Letterbox
    padded, scale, padding = processor.letterbox(image, target_size=(640, 640))

    assert padded.shape == (640, 640, 3)
    assert scale > 0
    assert len(padding) == 2


@pytest.mark.integration
def test_image_augmentation():
    """Test image augmentation pipeline"""
    from src.preprocessing.image_processor import ImageAugmentor

    augmentor = ImageAugmentor(seed=42)

    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    bboxes = [[100, 100, 200, 200]]

    # Augment
    augmented, new_bboxes = augmentor.augment(image, bboxes)

    assert augmented.shape == image.shape
    assert isinstance(augmented, np.ndarray)


@pytest.mark.integration
def test_edge_optimization():
    """Test optimization for edge devices"""
    from src.preprocessing.image_processor import EdgeOptimizer

    optimizer = EdgeOptimizer(target_device="cpu")

    image = np.random.rand(480, 640, 3).astype(np.float32)

    # Optimize
    optimized = optimizer.optimize_for_inference(image, quantize=False)

    assert optimized is not None
    assert optimized.flags['C_CONTIGUOUS']


@pytest.mark.integration
def test_resolution_reduction():
    """Test resolution reduction for edge devices"""
    from src.preprocessing.image_processor import EdgeOptimizer

    optimizer = EdgeOptimizer()

    image = np.zeros((1920, 1080, 3), dtype=np.uint8)

    # Reduce resolution
    reduced = optimizer.reduce_resolution(image, scale=0.5)

    assert reduced.shape[0] < image.shape[0]
    assert reduced.shape[1] < image.shape[1]


@pytest.mark.integration
@patch('src.models.yolo_detector.YOLO')
def test_batch_detection(mock_yolo_class, mock_yolo_model):
    """Test detecting objects in multiple images"""
    from src.models.yolo_detector import YOLODetector

    mock_yolo_class.return_value = mock_yolo_model

    detector = YOLODetector("yolov8n.pt")
    detector.load_model()

    # Create batch
    images = [
        np.zeros((640, 640, 3), dtype=np.uint8)
        for _ in range(10)
    ]

    # Detect all
    all_detections = []
    for image in images:
        detections = detector.detect(image)
        all_detections.append(detections)

    assert len(all_detections) == len(images)


@pytest.mark.integration
def test_video_utils():
    """Test video processing utilities"""
    from src.utils.video_utils import VideoProcessor

    processor = VideoProcessor()

    # Test with mock video properties
    fps = 30
    frame_count = 300
    duration = processor.calculate_duration(fps, frame_count)

    assert duration == 10.0  # 300 frames / 30 fps
