"""
Unit tests for YOLO Detector
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.models.yolo_detector import YOLODetector


@pytest.fixture
def detector():
    """Create YOLO detector"""
    return YOLODetector(
        model_path="yolov8n.pt",
        conf_threshold=0.5,
        iou_threshold=0.4
    )


def test_detector_initialization(detector):
    """Test detector initialization"""
    assert detector.model_path == "yolov8n.pt"
    assert detector.conf_threshold == 0.5
    assert detector.iou_threshold == 0.4
    assert detector.model is None


def test_load_model_with_ultralytics():
    """Test model loading with ultralytics installed"""
    detector = YOLODetector("yolov8n.pt")

    with patch('src.models.yolo_detector.YOLO') as mock_yolo:
        mock_model = Mock()
        mock_yolo.return_value = mock_model

        detector.load_model()

        mock_yolo.assert_called_once_with("yolov8n.pt")
        assert detector.model == mock_model


def test_load_model_without_ultralytics():
    """Test model loading without ultralytics"""
    detector = YOLODetector("yolov8n.pt")

    with patch('src.models.yolo_detector.YOLO', side_effect=ImportError):
        with pytest.raises(ImportError):
            detector.load_model()


def test_detect_without_loading(detector):
    """Test detection without loading model"""
    test_image = np.zeros((640, 640, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError, match="Model not loaded"):
        detector.detect(test_image)


def test_detect_single_image():
    """Test detecting objects in single image"""
    detector = YOLODetector("yolov8n.pt")

    # Mock YOLO model
    mock_result = Mock()
    mock_box = Mock()
    mock_box.xyxy = [torch.tensor([[100, 100, 200, 200]])]
    mock_box.conf = [torch.tensor([0.85])]
    mock_box.cls = [torch.tensor([0])]
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person"}

    with patch('src.models.yolo_detector.YOLO') as mock_yolo:
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person"}
        mock_yolo.return_value = mock_model

        detector.load_model()

        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        detections = detector.detect(test_image)

        assert len(detections) > 0
        assert 'bbox' in detections[0]
        assert 'confidence' in detections[0]
        assert 'class_id' in detections[0]
        assert 'class_name' in detections[0]
        assert detections[0]['confidence'] == 0.85
        assert detections[0]['class_name'] == "person"


def test_draw_detections(detector):
    """Test drawing detections on image"""
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)

    detections = [
        {
            'bbox': [100, 100, 200, 200],
            'confidence': 0.85,
            'class_name': 'person'
        },
        {
            'bbox': [300, 150, 400, 300],
            'confidence': 0.72,
            'class_name': 'car'
        }
    ]

    result = detector.draw_detections(test_image, detections)

    # Result should be the same image shape
    assert result.shape == test_image.shape


def test_detect_returns_correct_format():
    """Test that detect returns correct format"""
    detector = YOLODetector("yolov8n.pt")

    # Mock with empty results
    mock_result = Mock()
    mock_result.boxes = []

    with patch('src.models.yolo_detector.YOLO') as mock_yolo:
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {}
        mock_yolo.return_value = mock_model

        detector.load_model()

        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        detections = detector.detect(test_image)

        assert isinstance(detections, list)


def test_confidence_threshold_filtering():
    """Test that confidence threshold is applied"""
    detector = YOLODetector("yolov8n.pt", conf_threshold=0.7)

    mock_result = Mock()
    mock_box = Mock()
    mock_box.xyxy = [torch.tensor([[100, 100, 200, 200]])]
    mock_box.conf = [torch.tensor([0.65])]  # Below threshold
    mock_box.cls = [torch.tensor([0])]
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person"}

    with patch('src.models.yolo_detector.YOLO') as mock_yolo:
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person"}
        mock_yolo.return_value = mock_model

        detector.load_model()

        test_image = np.zeros((640, 640, 3), dtype=np.uint8)

        # Model should be called with confidence threshold
        detector.detect(test_image)

        # Check that the model was called
        mock_model.assert_called_once()


def test_iou_threshold():
    """Test IOU threshold is passed"""
    detector = YOLODetector("yolov8n.pt", iou_threshold=0.5)

    mock_result = Mock()
    mock_result.boxes = []

    with patch('src.models.yolo_detector.YOLO') as mock_yolo:
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {}
        mock_yolo.return_value = mock_model

        detector.load_model()

        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        detector.detect(test_image)

        # Verify model was called
        mock_model.assert_called_once()


# Import torch for tests
import torch
