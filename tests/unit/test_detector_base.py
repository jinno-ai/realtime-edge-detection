"""
Tests for AbstractDetector base class.

Test that the abstract interface is properly defined and enforces implementation.
"""

import pytest
import numpy as np
from typing import List, Dict, Any

from src.models.base import AbstractDetector


class ConcreteDetector(AbstractDetector):
    """Concrete implementation for testing AbstractDetector"""

    def load_model(self) -> None:
        """Mock implementation"""
        self.model = "mock_model"
        self.device = "cpu"
        self.class_names = ["person", "car", "dog"]

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Mock implementation"""
        return [
            {
                'class': 'person',
                'confidence': 0.89,
                'bbox': [10, 20, 100, 200]
            }
        ]

    def detect_batch(self, images: List[np.ndarray]) -> List[List[Dict[str, Any]]]:
        """Mock implementation"""
        return [self.detect(img) for img in images]

    def get_model_info(self) -> Dict[str, Any]:
        """Mock implementation"""
        return {
            'name': 'TestDetector',
            'version': '1.0.0',
            'classes': self.class_names,
            'input_size': (640, 640),
            'num_params': 1000
        }


class TestAbstractDetector:
    """Test AbstractDetector base class"""

    def test_cannot_instantiate_abstract_detector(self):
        """AbstractDetector cannot be instantiated directly"""
        with pytest.raises(TypeError):
            AbstractDetector({})

    def test_concrete_implementation_works(self):
        """Concrete implementation can be instantiated and used"""
        config = {'test': 'config'}
        detector = ConcreteDetector(config)

        assert detector.config == config
        assert detector.model is None
        assert detector.device is None
        assert detector.class_names == []

    def test_load_model_abstract_method(self):
        """Concrete class must implement load_model"""
        detector = ConcreteDetector({})

        detector.load_model()
        assert detector.model == "mock_model"
        assert detector.device == "cpu"
        assert detector.class_names == ["person", "car", "dog"]

    def test_detect_abstract_method(self):
        """Concrete class must implement detect"""
        detector = ConcreteDetector({})
        detector.load_model()

        image = np.zeros((640, 640, 3), dtype=np.uint8)
        detections = detector.detect(image)

        assert isinstance(detections, list)
        assert len(detections) == 1
        assert detections[0]['class'] == 'person'
        assert detections[0]['confidence'] == 0.89
        assert detections[0]['bbox'] == [10, 20, 100, 200]

    def test_detect_batch_abstract_method(self):
        """Concrete class must implement detect_batch"""
        detector = ConcreteDetector({})
        detector.load_model()

        images = [
            np.zeros((640, 640, 3), dtype=np.uint8),
            np.zeros((480, 640, 3), dtype=np.uint8)
        ]
        batch_results = detector.detect_batch(images)

        assert isinstance(batch_results, list)
        assert len(batch_results) == 2
        assert all(isinstance(results, list) for results in batch_results)
        assert len(batch_results[0]) == 1

    def test_get_model_info_abstract_method(self):
        """Concrete class must implement get_model_info"""
        detector = ConcreteDetector({})
        detector.load_model()

        info = detector.get_model_info()

        assert isinstance(info, dict)
        assert 'name' in info
        assert 'version' in info
        assert 'classes' in info
        assert 'input_size' in info
        assert info['name'] == 'TestDetector'

    def test_draw_detections_default_implementation(self):
        """Default draw_detections method should work"""
        detector = ConcreteDetector({})
        detector.load_model()

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = [
            {
                'class': 'person',
                'confidence': 0.89,
                'bbox': [10, 20, 100, 200]
            },
            {
                'class': 'car',
                'confidence': 0.75,
                'bbox': [200, 150, 400, 350]
            }
        ]

        output = detector.draw_detections(image, detections)

        # Should return a new array, not modify original
        assert output is not image
        assert output.shape == image.shape

        # Output should be different from input (drawn boxes)
        assert not np.array_equal(output, image)

    def test_draw_detections_without_confidence(self):
        """draw_detections can hide confidence scores"""
        detector = ConcreteDetector({})
        detector.load_model()

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = [
            {
                'class': 'person',
                'confidence': 0.89,
                'bbox': [10, 20, 100, 200]
            }
        ]

        output_with_conf = detector.draw_detections(image, detections, show_confidence=True)
        output_without_conf = detector.draw_detections(image, detections, show_confidence=False)

        # Both should be different from input
        assert not np.array_equal(output_with_conf, image)
        assert not np.array_equal(output_without_conf, image)

        # Outputs should differ based on show_confidence setting
        # (labels with/without confidence scores have different widths)
        assert not np.array_equal(output_with_conf, output_without_conf)

    def test_preprocess_default_implementation(self):
        """Default preprocess returns image unchanged"""
        detector = ConcreteDetector({})

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        processed = detector.preprocess(image)

        assert np.array_equal(processed, image)

    def test_postprocess_default_implementation(self):
        """Default postprocess returns empty list"""
        detector = ConcreteDetector({})

        raw_output = "mock_output"
        original_shape = (480, 640, 3)
        result = detector.postprocess(raw_output, original_shape)

        assert result == []

    def test_initialization_attributes(self):
        """Detector should initialize with correct attributes"""
        config = {'model': 'test', 'device': 'cpu'}
        detector = ConcreteDetector(config)

        assert detector.config == config
        assert detector.model is None
        assert detector.device is None
        assert detector.class_names == []
