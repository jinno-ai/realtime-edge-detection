"""
Unit tests for YOLODetector (P0 Critical Paths)

Tests cover:
- Model initialization with ConfigManager
- Model loading and error handling
- Detection execution and result parsing
- Error handling for edge cases
- Legacy deprecation warnings
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import warnings

from src.models.yolo_detector import YOLODetector
from src.config.config_manager import ConfigManager


@pytest.fixture
def sample_image():
    """Create sample image for testing"""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_yolo_model():
    """Create mock YOLO model with realistic results"""
    # Create mock result
    mock_result = Mock()
    mock_box = Mock()

    # Create mock tensors
    import torch
    mock_box.xyxy = [torch.tensor([[100, 100, 200, 200], [300, 150, 400, 300]])]
    mock_box.conf = [torch.tensor([0.85, 0.72])]
    mock_box.cls = [torch.tensor([0, 1])]

    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person", 1: "car", 2: "dog"}

    # Create mock model
    mock_model = Mock()
    mock_model.return_value = [mock_result]
    mock_model.names = {0: "person", 1: "car", 2: "dog"}

    return mock_model


class TestYOLODetectorInitialization:
    """
    P0: YOLODetector initialization with configuration
    Covers: Story 1.5, R-001
    """

    @pytest.mark.unit
    def test_initialize_with_default_config(self):
        """
        [P0] GIVEN: No configuration provided
        WHEN: YOLODetector is initialized
        THEN: Uses default configuration
        """
        # WHEN: Initializing without config
        detector = YOLODetector()

        # THEN: Default config values are used
        assert detector.model_path == 'yolov8n.pt'
        assert detector.conf_threshold == 0.5
        assert detector.iou_threshold == 0.4
        assert detector.max_detections == 100
        assert isinstance(detector.config, ConfigManager)

    @pytest.mark.unit
    def test_initialize_with_config_path(self, tmp_path):
        """
        [P0] GIVEN: Path to configuration file
        WHEN: YOLODetector is initialized with config path
        THEN: Loads configuration from file
        """
        # GIVEN: Config file
        import yaml
        config_file = tmp_path / "config.yaml"
        config_data = {
            'model': {'path': 'custom_model.pt'},
            'detection': {'confidence_threshold': 0.7, 'iou_threshold': 0.5}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # WHEN: Initializing with config path
        detector = YOLODetector(config=str(config_file))

        # THEN: Config values are loaded
        assert detector.model_path == 'custom_model.pt'
        assert detector.conf_threshold == 0.7
        assert detector.iou_threshold == 0.5

    @pytest.mark.unit
    def test_initialize_with_config_manager_instance(self):
        """
        [P0] GIVEN: A ConfigManager instance
        WHEN: YOLODetector is initialized with ConfigManager
        THEN: Uses provided ConfigManager
        """
        # GIVEN: ConfigManager instance
        config_mgr = ConfigManager()
        config_mgr._config['model']['path'] = 'manager_model.pt'

        # WHEN: Initializing with ConfigManager
        detector = YOLODetector(config=config_mgr)

        # THEN: Uses provided ConfigManager
        assert detector.config is config_mgr
        assert detector.model_path == 'manager_model.pt'

    @pytest.mark.unit
    def test_legacy_initialization_with_deprecation_warning(self):
        """
        [P0] GIVEN: Legacy parameters (model_path, conf_threshold, iou_threshold)
        WHEN: YOLODetector is initialized with legacy parameters
        THEN: Issues DeprecationWarning and overrides config
        """
        # GIVEN: Legacy parameters
        # WHEN: Initializing with legacy parameters
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            detector = YOLODetector(
                model_path='legacy_model.pt',
                conf_threshold=0.8,
                iou_threshold=0.6
            )

            # THEN: DeprecationWarning is issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert 'deprecated' in str(w[0].message).lower()

        # AND: Legacy parameters override defaults
        assert detector.model_path == 'legacy_model.pt'
        assert detector.conf_threshold == 0.8
        assert detector.iou_threshold == 0.6


class TestModelLoading:
    """
    P0: Model loading with error handling
    Covers: Story 1.3, R-003
    """

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_load_model_successfully(self, mock_yolo_class, mock_yolo_model):
        """
        [P0] GIVEN: YOLODetector instance and valid model path
        WHEN: load_model() is called
        THEN: Model is loaded successfully
        """
        # GIVEN: Mock YOLO class
        mock_yolo_class.return_value = mock_yolo_model

        # WHEN: Loading model
        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # THEN: Model is loaded
        assert detector.model is not None
        mock_yolo_class.assert_called_once_with('yolov8n.pt')

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO', side_effect=ImportError)
    def test_load_model_without_ultralytics_installed(self, mock_yolo):
        """
        [P0] GIVEN: ultralytics package is not installed
        WHEN: load_model() is called
        THEN: Raises ImportError with helpful message
        """
        # GIVEN: Ultralytics not installed (mocked)
        # WHEN: Loading model
        detector = YOLODetector(model_path='yolov8n.pt')

        # THEN: Raises ImportError
        with pytest.raises(ImportError):
            detector.load_model()


class TestObjectDetection:
    """
    P0: Object detection execution
    Covers: Story 1.5
    """

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_detect_objects_in_image(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: Loaded model and input image
        WHEN: detect() is called
        THEN: Returns list of detections with correct structure
        """
        # GIVEN: Mock model
        mock_yolo_class.return_value = mock_yolo_model

        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # WHEN: Detecting objects
        detections = detector.detect(sample_image)

        # THEN: Returns list of detections
        assert isinstance(detections, list)
        assert len(detections) > 0

        # AND: Each detection has correct structure
        det = detections[0]
        assert 'bbox' in det
        assert 'confidence' in det
        assert 'class_id' in det
        assert 'class_name' in det

        # AND: Values have correct types
        assert isinstance(det['bbox'], list)
        assert len(det['bbox']) == 4  # [x1, y1, x2, y2]
        assert isinstance(det['confidence'], float)
        assert isinstance(det['class_id'], int)
        assert isinstance(det['class_name'], str)

    @pytest.mark.unit
    def test_detect_without_loading_model_raises_error(self, sample_image):
        """
        [P0] GIVEN: YOLODetector instance
        WHEN: detect() is called before load_model()
        THEN: Raises RuntimeError with clear message
        """
        # GIVEN: Detector without loaded model
        detector = YOLODetector()
        detector.model = None  # Explicitly not loaded

        # WHEN: Trying to detect
        # THEN: Raises RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            detector.detect(sample_image)

        assert 'not loaded' in str(exc_info.value).lower()

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_detect_respects_max_detections_limit(self, mock_yolo_class, sample_image):
        """
        [P0] GIVEN: Model with max_detections limit
        WHEN: detect() returns more detections than limit
        THEN: Returns only max_detections results
        """
        # GIVEN: Mock model that returns many detections
        mock_result = Mock()
        mock_box = Mock()

        import torch
        # Create 200 mock detections
        mock_box.xyxy = [torch.tensor([[i*10, i*10, (i+1)*10, (i+1)*10] for i in range(200)])]
        mock_box.conf = [torch.tensor([0.5] * 200)]
        mock_box.cls = [torch.tensor([0] * 200)]

        mock_result.boxes = [mock_box]
        mock_result.names = {0: "person"}

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person"}

        mock_yolo_class.return_value = mock_model

        # WHEN: Detecting with max_detections=100
        detector = YOLODetector(config=ConfigManager())
        detector.max_detections = 100  # Set limit
        detector.load_model()

        detections = detector.detect(sample_image)

        # THEN: Returns at most 100 detections
        assert len(detections) <= 100

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_detect_with_no_detections(self, mock_yolo_class, sample_image):
        """
        [P0] GIVEN: Image with no detectable objects
        WHEN: detect() is called
        THEN: Returns empty list
        """
        # GIVEN: Mock model with no detections
        mock_result = Mock()
        mock_result.boxes = []  # No detections
        mock_result.names = {0: "person"}

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person"}

        mock_yolo_class.return_value = mock_model

        # WHEN: Detecting
        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()
        detections = detector.detect(sample_image)

        # THEN: Returns empty list
        assert isinstance(detections, list)
        assert len(detections) == 0

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_detect_uses_configured_thresholds(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: YOLODetector with custom confidence and IOU thresholds
        WHEN: detect() is called
        THEN: Uses configured thresholds for inference
        """
        # GIVEN: Mock model
        mock_yolo_class.return_value = mock_yolo_model

        # WHEN: Detecting with custom thresholds
        detector = YOLODetector(
            config=ConfigManager()
        )
        detector.conf_threshold = 0.75
        detector.iou_threshold = 0.55
        detector.load_model()

        detections = detector.detect(sample_image)

        # THEN: Model was called with correct thresholds
        call_args = mock_yolo_model.call_args
        # Check that conf and iou were passed
        assert 'conf' in call_args[1] or len(call_args[0]) > 1
        assert 'iou' in call_args[1] or len(call_args[0]) > 2


class TestDetectionResultParsing:
    """
    P0: Detection result parsing and conversion
    Covers: Story 1.5
    """

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_parse_bbox_coordinates_correctly(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: Model returns bbox in xyxy format
        WHEN: detect() parses results
        THEN: Bbox coordinates are converted to list of floats
        """
        # GIVEN: Mock model
        mock_yolo_class.return_value = mock_yolo_model

        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # WHEN: Detecting
        detections = detector.detect(sample_image)

        # THEN: Bbox coordinates are floats
        bbox = detections[0]['bbox']
        assert all(isinstance(coord, float) for coord in bbox)

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_parse_confidence_scores_as_float(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: Model returns confidence scores
        WHEN: detect() parses results
        THEN: Confidence is converted to float
        """
        # GIVEN: Mock model
        mock_yolo_class.return_value = mock_yolo_model

        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # WHEN: Detecting
        detections = detector.detect(sample_image)

        # THEN: Confidence is float
        confidence = detections[0]['confidence']
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_parse_class_id_as_int(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: Model returns class IDs
        WHEN: detect() parses results
        THEN: Class ID is converted to int
        """
        # GIVEN: Mock model
        mock_yolo_class.return_value = mock_yolo_model

        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # WHEN: Detecting
        detections = detector.detect(sample_image)

        # THEN: Class ID is int
        class_id = detections[0]['class_id']
        assert isinstance(class_id, int)

    @pytest.mark.unit
    @patch('src.models.yolo_detector.YOLO')
    def test_map_class_id_to_class_name(self, mock_yolo_class, mock_yolo_model, sample_image):
        """
        [P0] GIVEN: Model returns class IDs and has class names mapping
        WHEN: detect() parses results
        THEN: Class ID is mapped to class name
        """
        # GIVEN: Mock model with names mapping
        mock_yolo_class.return_value = mock_yolo_model

        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        # WHEN: Detecting
        detections = detector.detect(sample_image)

        # THEN: Class name is populated
        class_name = detections[0]['class_name']
        assert isinstance(class_name, str)
        assert class_name in ['person', 'car', 'dog']


class TestErrorHandling:
    """
    P0: Error handling for edge cases
    Covers: Story 1.5
    """

    @pytest.mark.unit
    def test_detect_with_invalid_image_format(self):
        """
        [P0] GIVEN: Invalid input (not numpy array)
        WHEN: detect() is called
        THEN: Raises appropriate error
        """
        # GIVEN: Detector with loaded model (mocked)
        detector = YOLODetector()
        detector.model = Mock()

        # WHEN: Passing invalid input
        invalid_inputs = [
            None,
            "not_an_image",
            123,
            {'image': 'invalid'},
            []
        ]

        for invalid_input in invalid_inputs:
            # THEN: Should raise error
            with pytest.raises((AttributeError, TypeError, RuntimeError)):
                detector.detect(invalid_input)

    @pytest.mark.unit
    def test_detect_with_empty_image(self):
        """
        [P0] GIVEN: Empty numpy array (0x0x3)
        WHEN: detect() is called
        THEN: Handles gracefully or raises clear error
        """
        # GIVEN: Empty image
        empty_image = np.array([], dtype=np.uint8).reshape(0, 0, 3)

        detector = YOLODetector()
        detector.model = Mock()
        detector.model.return_value = []  # No results

        # WHEN: Detecting
        detections = detector.detect(empty_image)

        # THEN: Returns empty list (doesn't crash)
        assert isinstance(detections, list)

    @pytest.mark.unit
    def test_detect_with_grayscale_image(self):
        """
        [P0] GIVEN: Grayscale image (single channel)
        WHEN: detect() is called
        THEN: Handles correctly (converts or raises clear error)
        """
        # GIVEN: Grayscale image
        gray_image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)

        detector = YOLODetector()
        detector.model = Mock()
        detector.model.return_value = []

        # WHEN: Detecting
        # May raise error or handle conversion
        try:
            detections = detector.detect(gray_image)
            assert isinstance(detections, list)
        except (ValueError, RuntimeError) as e:
            # Acceptable if error message is clear
            assert 'channel' in str(e).lower() or 'grayscale' in str(e).lower()


class TestVideoDetection:
    """
    P0: Video detection pipeline
    Covers: Story 1.5
    """

    @pytest.mark.unit
    @patch('cv2.VideoWriter')
    @patch('cv2.VideoCapture')
    @patch('src.models.yolo_detector.YOLO')
    def test_detect_video_with_output(self, mock_yolo_class, mock_yolo_model,
                                      mock_video_capture, mock_video_writer, tmp_path):
        """
        [P0] GIVEN: Video file path and output path
        WHEN: detect_video() is called
        THEN: Processes video and writes to output file
        """
        # GIVEN: Mock video capture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (False, None)  # End of video
        ]
        mock_cap.get.side_effect = lambda x: {
            0: 30,  # CAP_PROP_FPS
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480   # CAP_PROP_FRAME_HEIGHT
        }.get(x, 0)
        mock_video_capture.return_value = mock_cap

        # Mock YOLO
        mock_yolo_class.return_value = mock_yolo_model

        # WHEN: Detecting video
        detector = YOLODetector(model_path='yolov8n.pt')
        detector.load_model()

        output_path = str(tmp_path / "output.mp4")
        detector.detect_video('input.mp4', output_path)

        # THEN: Video was processed
        assert mock_cap.read.called
        mock_cap.release.assert_called()
        mock_video_writer.return_value.release.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'unit'])
