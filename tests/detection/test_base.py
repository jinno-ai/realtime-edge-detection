"""
Tests for the abstract detector base class.
"""

import pytest
import numpy as np
from src.detection.base import AbstractDetector, DetectionResult, ModelInfo


class DummyDetector(AbstractDetector):
    """Dummy detector implementation for testing."""

    def load_model(self, model_path: str, device: str = "cpu") -> None:
        """Dummy load implementation."""
        self._model = {"path": model_path, "device": device}
        self._model_path = model_path
        self._device = device

    def detect(self, image: np.ndarray) -> DetectionResult:
        """Dummy detect implementation."""
        self._ensure_loaded()
        return DetectionResult(
            boxes=np.array([[10, 20, 30, 40]]),
            scores=np.array([0.95]),
            classes=np.array([0]),
        )

    def detect_batch(self, images: list) -> list:
        """Dummy detect_batch implementation."""
        self._ensure_loaded()
        return [self.detect(images[0]) for _ in images]

    def get_model_info(self) -> ModelInfo:
        """Dummy get_model_info implementation."""
        self._ensure_loaded()
        return ModelInfo(
            name="dummy",
            version="1.0",
            input_size=(640, 640),
            class_names=["class1", "class2"],
        )


class TestDetectionResult:
    """Test DetectionResult dataclass."""

    def test_valid_detection_result(self):
        """Test creating a valid DetectionResult."""
        result = DetectionResult(
            boxes=np.array([[10, 20, 30, 40]]),
            scores=np.array([0.95]),
            classes=np.array([0]),
        )
        assert result.boxes.shape == (1, 4)
        assert result.scores.shape == (1,)
        assert result.classes.shape == (1,)

    def test_mismatched_array_lengths(self):
        """Test that mismatched array lengths raise an error."""
        with pytest.raises(ValueError, match="Mismatch in array lengths"):
            DetectionResult(
                boxes=np.array([[10, 20, 30, 40]]),
                scores=np.array([0.95, 0.85]),  # Wrong length
                classes=np.array([0]),
            )

    def test_invalid_boxes_shape(self):
        """Test that invalid box shape raises an error."""
        with pytest.raises(ValueError, match="Boxes must have shape"):
            DetectionResult(
                boxes=np.array([[10, 20, 30]]),  # Wrong shape
                scores=np.array([0.95]),
                classes=np.array([0]),
            )

    def test_default_metadata(self):
        """Test that default metadata is an empty dict."""
        result = DetectionResult(
            boxes=np.array([[10, 20, 30, 40]]),
            scores=np.array([0.95]),
            classes=np.array([0]),
        )
        assert result.metadata == {}


class TestModelInfo:
    """Test ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating a ModelInfo object."""
        info = ModelInfo(
            name="yolov8n",
            version="2.0.0",
            input_size=(640, 640),
            class_names=["person", "car", "dog"],
        )
        assert info.name == "yolov8n"
        assert info.version == "2.0.0"
        assert info.input_size == (640, 640)
        assert info.class_names == ["person", "car", "dog"]

    def test_model_info_optional_fields(self):
        """Test ModelInfo with optional fields."""
        info = ModelInfo(name="custom")
        assert info.name == "custom"
        assert info.version is None
        assert info.input_size is None
        assert info.class_names is None


class TestAbstractDetector:
    """Test AbstractDetector base class."""

    def test_cannot_instantiate_abstract_detector(self):
        """Test that AbstractDetector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AbstractDetector()

    def test_detector_must_implement_all_methods(self):
        """Test that detectors must implement all abstract methods."""
        # This should raise TypeError if methods are missing
        # DummyDetector implements all methods, so this should work
        detector = DummyDetector()
        assert isinstance(detector, AbstractDetector)

    def test_is_loaded_property(self):
        """Test the is_loaded property."""
        detector = DummyDetector()
        assert not detector.is_loaded

        detector.load_model("test.pt", "cpu")
        assert detector.is_loaded

    def test_detect_without_loading_raises_error(self):
        """Test that detect without loading raises RuntimeError."""
        detector = DummyDetector()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect(np.zeros((640, 640, 3), dtype=np.uint8))

    def test_detect_batch_without_loading_raises_error(self):
        """Test that detect_batch without loading raises RuntimeError."""
        detector = DummyDetector()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect_batch([np.zeros((640, 640, 3), dtype=np.uint8)])

    def test_get_model_info_without_loading_raises_error(self):
        """Test that get_model_info without loading raises RuntimeError."""
        detector = DummyDetector()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.get_model_info()

    def test_detect_returns_valid_result(self):
        """Test that detect returns a valid DetectionResult."""
        detector = DummyDetector()
        detector.load_model("test.pt", "cpu")

        result = detector.detect(np.zeros((640, 640, 3), dtype=np.uint8))
        assert isinstance(result, DetectionResult)
        assert result.boxes.shape == (1, 4)

    def test_detect_batch_returns_list_of_results(self):
        """Test that detect_batch returns a list of DetectionResults."""
        detector = DummyDetector()
        detector.load_model("test.pt", "cpu")

        images = [np.zeros((640, 640, 3), dtype=np.uint8) for _ in range(3)]
        results = detector.detect_batch(images)

        assert len(results) == 3
        assert all(isinstance(r, DetectionResult) for r in results)

    def test_get_model_info_returns_model_info(self):
        """Test that get_model_info returns a ModelInfo object."""
        detector = DummyDetector()
        detector.load_model("test.pt", "cpu")

        info = detector.get_model_info()
        assert isinstance(info, ModelInfo)
        assert info.name == "dummy"
