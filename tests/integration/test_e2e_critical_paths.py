"""
End-to-End Integration Tests (P0 Critical Paths)

Tests cover:
- Complete configuration loading and validation workflow
- Full detection pipeline with real model loading (mocked)
- Video processing pipeline
- Error recovery and graceful degradation
- Configuration profile switching
"""

import pytest
import numpy as np
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.config import ConfigManager
from src.models.yolo_detector import YOLODetector
from src.preprocessing.image_processor import ImageProcessor


@pytest.mark.integration
class TestConfigurationE2E:
    """
    E2E: Configuration management workflow
    Covers: Story 1.1, 1.2, R-001, R-004, R-006, R-007
    """

    @pytest.mark.integration
    def test_full_config_loading_workflow(self, tmp_path):
        """
        [P0] GIVEN: Multiple config sources (file, profile, env vars)
        WHEN: ConfigManager loads configuration
        THEN: All sources merged with correct priority (env > profile > file > defaults)
        """
        # GIVEN: Default config file
        default_config = {
            'model': {'type': 'yolo_v8', 'path': 'default.pt'},
            'detection': {'confidence_threshold': 0.5, 'iou_threshold': 0.4}
        }
        default_file = tmp_path / "default.yaml"
        with open(default_file, 'w') as f:
            yaml.dump(default_config, f)

        # AND: User config file
        user_config = {
            'model': {'path': 'user.pt'},
            'detection': {'confidence_threshold': 0.6}
        }
        user_file = tmp_path / "config.yaml"
        with open(user_file, 'w') as f:
            yaml.dump(user_config, f)

        # AND: Profile config
        profile_config = {
            'detection': {'iou_threshold': 0.5}
        }
        profile_file = tmp_path / "prod.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(profile_config, f)

        # AND: Environment variable
        import os
        os.environ['EDGE_DETECTION_MODEL_PATH'] = 'env.pt'

        # WHEN: Loading config with all sources
        config_mgr = ConfigManager(
            config_path=str(user_file),
            default_config=str(default_file)
        )
        config_mgr.config_dir = tmp_path
        config = config_mgr.load_config()

        # THEN: Priority order respected
        assert config['model']['path'] == 'env.pt'  # Env var highest
        assert config['detection']['confidence_threshold'] == 0.6  # User file
        assert config['detection']['iou_threshold'] == 0.5  # Profile
        assert config['model']['type'] == 'yolo_v8'  # Default (not overridden)

        # Cleanup
        del os.environ['EDGE_DETECTION_MODEL_PATH']

    @pytest.mark.integration
    def test_config_validation_blocks_invalid_values(self, tmp_path):
        """
        [P0] GIVEN: Configuration file with invalid values
        WHEN: ConfigManager loads and validates configuration
        THEN: Validation errors are raised with clear messages
        """
        # GIVEN: Invalid config file
        invalid_config = {
            'detection': {
                'confidence_threshold': 1.5,  # Invalid: > 1.0
                'iou_threshold': -0.5         # Invalid: < 0.0
            }
        }
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(invalid_config, f)

        # WHEN: Loading config
        config_mgr = ConfigManager(config_path=str(config_file))
        config = config_mgr.load_config()

        # THEN: Validation fails with errors
        is_valid = config_mgr.validate()
        assert is_valid is False

        errors = config_mgr.get_validation_errors()
        assert len(errors) >= 2

        # AND: Errors include hints
        error_messages = ' '.join(errors)
        assert 'confidence_threshold' in error_messages
        assert 'iou_threshold' in error_messages

    @pytest.mark.integration
    def test_profile_switching_workflow(self, tmp_path):
        """
        [P0] GIVEN: Multiple configuration profiles
        WHEN: User switches between profiles
        THEN: Configuration changes correctly without errors
        """
        # GIVEN: Dev and prod profiles
        dev_profile = {
            'device': {'type': 'cpu'},
            'detection': {'confidence_threshold': 0.3}
        }
        (tmp_path / "dev.yaml").write_text(yaml.dump(dev_profile))

        prod_profile = {
            'device': {'type': 'cuda'},
            'detection': {'confidence_threshold': 0.7}
        }
        (tmp_path / "prod.yaml").write_text(yaml.dump(prod_profile))

        # WHEN: Loading dev profile
        config_mgr = ConfigManager(profile='dev')
        config_mgr.config_dir = tmp_path
        dev_config = config_mgr.load_config()

        # THEN: Dev settings loaded
        assert dev_config['device']['type'] == 'cpu'
        assert dev_config['detection']['confidence_threshold'] == 0.3

        # WHEN: Switching to prod profile
        config_mgr_prod = ConfigManager(profile='prod')
        config_mgr_prod.config_dir = tmp_path
        prod_config = config_mgr_prod.load_config()

        # THEN: Prod settings loaded
        assert prod_config['device']['type'] == 'cuda'
        assert prod_config['detection']['confidence_threshold'] == 0.7


@pytest.mark.integration
class TestDetectionPipelineE2E:
    """
    E2E: Object detection pipeline
    Covers: Story 1.5, R-002, R-003
    """

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_complete_detection_workflow(self, mock_yolo_class, tmp_path):
        """
        [P0] GIVEN: Configuration file and YOLO model
        WHEN: Full detection pipeline executes
        THEN: Image is processed and detections returned
        """
        # GIVEN: Configuration file
        config_file = tmp_path / "config.yaml"
        config_data = {
            'model': {'path': 'yolov8n.pt'},
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4,
                'max_detections': 100
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # AND: Mock YOLO model
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

        # WHEN: Loading config and initializing detector
        config_mgr = ConfigManager(config_path=str(config_file))
        config = config_mgr.load_config()

        detector = YOLODetector(config=config_mgr)
        detector.load_model()

        # AND: Processing image
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        detections = detector.detect(test_image)

        # THEN: Detections returned successfully
        assert isinstance(detections, list)
        assert len(detections) > 0

        # AND: Detection has correct structure
        det = detections[0]
        assert 'bbox' in det
        assert 'confidence' in det
        assert 'class_name' in det
        assert det['confidence'] >= 0.5  # Respects threshold

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_detection_with_configured_thresholds(self, mock_yolo_class, tmp_path):
        """
        [P0] GIVEN: Configuration with specific confidence and IOU thresholds
        WHEN: Detector processes images
        THEN: Model uses configured thresholds
        """
        # GIVEN: Config with custom thresholds
        config_file = tmp_path / "config.yaml"
        config_data = {
            'detection': {
                'confidence_threshold': 0.75,
                'iou_threshold': 0.55
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # AND: Mock model
        mock_model = Mock()
        mock_result = Mock()
        mock_result.boxes = []
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        # WHEN: Loading config and detecting
        config_mgr = ConfigManager(config_path=str(config_file))
        detector = YOLODetector(config=config_mgr)
        detector.load_model()

        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        detector.detect(test_image)

        # THEN: Model called with configured thresholds
        mock_model.assert_called_once()
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs['conf'] == 0.75
        assert call_kwargs['iou'] == 0.55

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO')
    def test_detection_with_max_detections_limit(self, mock_yolo_class):
        """
        [P0] GIVEN: Configuration with max_detections limit
        WHEN: Model returns more detections than limit
        THEN: Only max_detections results are returned
        """
        # GIVEN: Config with low max_detections
        config_mgr = ConfigManager()
        config_mgr._config['detection']['max_detections'] = 5

        # AND: Mock model returning many detections
        mock_result = Mock()
        mock_box = Mock()
        import torch
        # Return 20 detections
        mock_box.xyxy = [torch.tensor([[i * 10, i * 10, (i + 1) * 10, (i + 1) * 10]
                                      for i in range(20)])]
        mock_box.conf = [torch.tensor([0.9] * 20)]
        mock_box.cls = [torch.tensor([0] * 20)]
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "person"}

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        # WHEN: Detecting
        detector = YOLODetector(config=config_mgr)
        detector.load_model()

        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        detections = detector.detect(test_image)

        # THEN: Returns at most max_detections
        assert len(detections) <= 5


@pytest.mark.integration
class TestVideoProcessingE2E:
    """
    E2E: Video processing pipeline
    Covers: Story 1.5
    """

    @pytest.mark.integration
    @patch('cv2.VideoWriter')
    @patch('cv2.VideoCapture')
    @patch('src.models.yolo_detector.YOLO')
    def test_video_detection_workflow(self, mock_yolo_class, mock_video_capture,
                                     mock_video_writer, tmp_path):
        """
        [P0] GIVEN: Video file and output path
        WHEN: detect_video() is called
        THEN: Video is processed frame by frame and written to output
        """
        # GIVEN: Config file
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({'model': {'path': 'yolov8n.pt'}}, f)

        # AND: Mock video capture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(10)
        ]
        mock_cap.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
        mock_cap.get.side_effect = lambda prop: {
            0: 30,  # CAP_PROP_FPS
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480   # CAP_PROP_FRAME_HEIGHT
        }.get(prop, 0)
        mock_video_capture.return_value = mock_cap

        # AND: Mock YOLO
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        # WHEN: Processing video
        config_mgr = ConfigManager(config_path=str(config_file))
        detector = YOLODetector(config=config_mgr)
        detector.load_model()

        input_video = "input.mp4"
        output_video = str(tmp_path / "output.mp4")
        detector.detect_video(input_video, output_video)

        # THEN: Video was processed
        assert mock_cap.read.call_count >= 10
        mock_cap.release.assert_called()

        # AND: Output video writer was created and released
        mock_video_writer.assert_called_once()
        mock_video_writer.return_value.release.assert_called()

    @pytest.mark.integration
    @patch('cv2.VideoWriter')
    @patch('cv2.VideoCapture')
    @patch('src.models.yolo_detector.YOLO')
    def test_video_processing_with_fps_calculation(self, mock_yolo_class,
                                                   mock_video_capture,
                                                   mock_video_writer):
        """
        [P0] GIVEN: Video with known FPS and frame count
        WHEN: Video is processed
        THEN: Average FPS is calculated and reported
        """
        # GIVEN: Mock video
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 30,  # 30 FPS
            3: 640,
            4: 480
        }.get(prop, 0)

        # Return 90 frames (3 seconds at 30 FPS)
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                 for _ in range(90)]
        mock_cap.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
        mock_video_capture.return_value = mock_cap

        # AND: Mock model
        mock_result = Mock()
        mock_result.boxes = []
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        # WHEN: Processing video
        detector = YOLODetector()
        detector.model = mock_model

        with patch('builtins.print') as mock_print:
            detector.detect_video("input.mp4", "output.mp4")

        # THEN: FPS is calculated and printed
        # Check that print was called with FPS info
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any('FPS' in call or 'fps' in call for call in print_calls)


@pytest.mark.integration
class TestErrorRecoveryE2E:
    """
    E2E: Error recovery and graceful degradation
    Covers: R-002, NFR-R2 (graceful error handling)
    """

    @pytest.mark.integration
    def test_missing_config_file_uses_defaults(self):
        """
        [P0] GIVEN: No configuration file exists
        WHEN: ConfigManager is initialized
        THEN: Uses defaults without crashing
        """
        # GIVEN: No config file (clean directory)

        # WHEN: Initializing ConfigManager
        config_mgr = ConfigManager()
        config = config_mgr.load_config()

        # THEN: Defaults loaded successfully
        assert config['model']['type'] == 'yolo_v8'
        assert config['detection']['confidence_threshold'] == 0.5

    @pytest.mark.integration
    def test_invalid_yaml_with_clear_error_message(self, tmp_path):
        """
        [P0] GIVEN: YAML file with syntax error
        WHEN: ConfigManager tries to load it
        THEN: Raises error with line number and fix hint
        """
        # GIVEN: Invalid YAML
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("model:\n  type: yolo_v8\n    path: bad  # Bad indent")

        # WHEN: Loading
        config_mgr = ConfigManager(config_path=str(invalid_file))

        # THEN: Raises clear error
        from src.core.errors import EdgeDetectionError
        with pytest.raises(EdgeDetectionError) as exc_info:
            config_mgr.load_config()

        error = exc_info.value
        assert 'Invalid YAML syntax' in str(error)
        assert error.hint is not None

    @pytest.mark.integration
    @patch('src.models.yolo_detector.YOLO', side_effect=ImportError("No module named 'ultralytics'"))
    def test_missing_ultralytics_with_helpful_message(self, mock_yolo):
        """
        [P0] GIVEN: ultralytics package not installed
        WHEN: YOLODetector tries to load model
        THEN: Raises ImportError with installation instructions
        """
        # GIVEN: No ultralytics installed (mocked)
        # WHEN: Loading model
        detector = YOLODetector()

        # THEN: Raises ImportError with helpful message
        with pytest.raises(ImportError):
            detector.load_model()

    @pytest.mark.integration
    def test_detect_without_loaded_model_raises_clear_error(self):
        """
        [P0] GIVEN: Detector without loaded model
        WHEN: detect() is called
        THEN: Raises RuntimeError with clear message
        """
        # GIVEN: Detector without model
        detector = YOLODetector()
        detector.model = None

        # WHEN: Trying to detect
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # THEN: Raises clear error
        with pytest.raises(RuntimeError) as exc_info:
            detector.detect(test_image)

        assert 'not loaded' in str(exc_info.value).lower()


@pytest.mark.integration
class TestImagePreprocessingE2E:
    """
    E2E: Image preprocessing pipeline
    Covers: Story 1.5
    """

    @pytest.mark.integration
    def test_letterbox_preprocessing_workflow(self):
        """
        [P0] GIVEN: Image of arbitrary size
        WHEN: Letterbox preprocessing is applied
        THEN: Image is resized to target size with padding
        """
        # GIVEN: Image of arbitrary size
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # WHEN: Applying letterbox
        processor = ImageProcessor(target_size=(640, 640))
        padded, scale, padding = processor.letterbox(image, target_size=(640, 640))

        # THEN: Image resized correctly
        assert padded.shape == (640, 640, 3)
        assert scale > 0
        assert len(padding) == 2
        assert isinstance(padding[0], tuple)  # (top, bottom) padding
        assert isinstance(padding[1], tuple)  # (left, right) padding

    @pytest.mark.integration
    def test_batch_preprocessing_workflow(self):
        """
        [P0] GIVEN: Multiple images of different sizes
        WHEN: Batch preprocessing is applied
        THEN: All images processed to same size
        """
        # GIVEN: Images of different sizes
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8),
            np.random.randint(0, 255, (360, 480, 3), dtype=np.uint8)
        ]

        # WHEN: Batch preprocessing
        processor = ImageProcessor(target_size=(640, 640))
        batch = processor.batch_preprocess(images)

        # THEN: All images same size
        assert batch.shape[0] == len(images)
        assert batch.shape[1:] == (3, 640, 640) or batch.shape[1:] == (640, 640, 3)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
