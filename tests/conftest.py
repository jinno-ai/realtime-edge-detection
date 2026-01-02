"""
Shared pytest fixtures and configuration for edge detection tests
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import yaml


# ============================================================================
# Image Fixtures
# ============================================================================

@pytest.fixture
def sample_image_bgr():
    """Create a sample BGR image (OpenCV format)"""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_rgb():
    """Create a sample RGB image"""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_grayscale():
    """Create a sample grayscale image"""
    return np.random.randint(0, 255, (480, 640), dtype=np.uint8)


@pytest.fixture
def sample_images_batch():
    """Create a batch of sample images"""
    return [
        np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        for _ in range(5)
    ]


@pytest.fixture
def sample_bboxes():
    """Create sample bounding boxes [x1, y1, x2, y2]"""
    return [
        [100, 100, 200, 200],
        [300, 150, 400, 300],
        [50, 50, 150, 150]
    ]


# ============================================================================
# Model/Detection Fixtures
# ============================================================================

@pytest.fixture
def mock_yolo_result():
    """Create mock YOLO detection result"""
    mock_result = Mock()
    mock_box = Mock()

    # Mock tensor values
    import torch
    mock_box.xyxy = [torch.tensor([[100, 100, 200, 200]])]
    mock_box.conf = [torch.tensor([0.85])]
    mock_box.cls = [torch.tensor([0])]

    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person", 1: "car", 2: "dog"}

    return mock_result


@pytest.fixture
def mock_yolo_model(mock_yolo_result):
    """Create mock YOLO model"""
    mock_model = Mock()
    mock_model.return_value = [mock_yolo_result]
    mock_model.names = {0: "person", 1: "car", 2: "dog"}
    return mock_model


@pytest.fixture
def sample_detections():
    """Create sample detection results"""
    return [
        {
            'bbox': [100, 100, 200, 200],
            'confidence': 0.85,
            'class_id': 0,
            'class_name': 'person'
        },
        {
            'bbox': [300, 150, 400, 300],
            'confidence': 0.72,
            'class_id': 1,
            'class_name': 'car'
        }
    ]


# ============================================================================
# Config File Fixtures
# ============================================================================

@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary YAML config file"""
    config_file = tmp_path / "test_config.yaml"
    config_content = {
        'model': {
            'type': 'yolo_v8',
            'path': 'yolov8n.pt'
        },
        'detection': {
            'confidence_threshold': 0.5,
            'iou_threshold': 0.4,
            'max_detections': 100
        },
        'preprocessing': {
            'target_size': [640, 640],
            'normalize': True
        }
    }
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)
    return str(config_file)


@pytest.fixture
def invalid_config_file(tmp_path):
    """Create invalid YAML config for error testing"""
    config_file = tmp_path / "invalid_config.yaml"
    with open(config_file, 'w') as f:
        f.write("model:\n  type: yolo_v8\n    path: bad  # Invalid indentation")
    return str(config_file)


# ============================================================================
# Video Fixtures
# ============================================================================

@pytest.fixture
def sample_video_params():
    """Create sample video parameters"""
    return {
        'fps': 30,
        'frame_count': 300,
        'width': 640,
        'height': 480,
        'duration': 10.0
    }


@pytest.fixture
def temp_video_file(tmp_path):
    """Create temporary video file path"""
    return str(tmp_path / "test_video.mp4")


# ============================================================================
# Temp Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, may require external deps)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (performance, stress tests)"
    )
    config.addinivalue_line(
        "markers", "gpu: Tests that require GPU (should be skipped on CPU-only systems)"
    )
