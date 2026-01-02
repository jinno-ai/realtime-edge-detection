"""
Factory functions for generating test configuration data

Uses faker for realistic test data generation
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import yaml


class ConfigFactory:
    """
    Factory for creating test configuration data

    Generates realistic, varied configuration data for testing.
    Supports overrides for specific test scenarios.
    """

    @staticmethod
    def create_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a valid configuration dictionary

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Valid configuration dictionary
        """
        config = {
            'model': {
                'type': 'yolo_v8',
                'path': 'yolov8n.pt',
                'download': True,
                'cache_dir': '~/.cache/edge-detection'
            },
            'device': {
                'type': 'auto',
                'optimize': True,
                'quantization': None
            },
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4,
                'max_detections': 100,
                'batch_size': 1
            },
            'logging': {
                'level': 'INFO',
                'format': 'json',
                'file': None,
                'rotation': '10MB'
            },
            'metrics': {
                'enabled': True,
                'export': 'prometheus',
                'port': 9090
            }
        }

        # Apply overrides using deep merge
        if overrides:
            ConfigFactory._deep_merge(config, overrides)

        return config

    @staticmethod
    def create_invalid_config(error_type: str) -> Dict[str, Any]:
        """
        Create an invalid configuration for testing error handling

        Args:
            error_type: Type of error to generate
                - 'high_confidence': confidence_threshold > 1.0
                - 'low_confidence': confidence_threshold < 0.0
                - 'high_iou': iou_threshold > 1.0
                - 'low_iou': iou_threshold < 0.0
                - 'invalid_device': invalid device type
                - 'invalid_log_level': invalid logging level
                - 'invalid_port': port out of range
                - 'empty_model_path': empty string for model path

        Returns:
            Invalid configuration dictionary
        """
        configs = {
            'high_confidence': {
                'detection': {'confidence_threshold': 1.5}
            },
            'low_confidence': {
                'detection': {'confidence_threshold': -0.5}
            },
            'high_iou': {
                'detection': {'iou_threshold': 1.2}
            },
            'low_iou': {
                'detection': {'iou_threshold': -0.3}
            },
            'invalid_device': {
                'device': {'type': 'invalid_device_type'}
            },
            'invalid_log_level': {
                'logging': {'level': 'INVALID_LEVEL'}
            },
            'invalid_port': {
                'metrics': {'port': 100}  # Too low
            },
            'empty_model_path': {
                'model': {'path': ''}
            }
        }

        if error_type not in configs:
            raise ValueError(f"Unknown error type: {error_type}")

        return configs[error_type]

    @staticmethod
    def create_config_file(tmp_dir: Path,
                          filename: str = 'test_config.yaml',
                          overrides: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a temporary YAML configuration file

        Args:
            tmp_dir: Temporary directory path
            filename: Name of config file
            overrides: Configuration overrides

        Returns:
            Absolute path to created file
        """
        config = ConfigFactory.create_config(overrides)

        config_file = tmp_dir / filename
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        return str(config_file)

    @staticmethod
    def create_invalid_yaml_file(tmp_dir: Path,
                                 error_type: str = 'indentation') -> str:
        """
        Create an invalid YAML file for error testing

        Args:
            tmp_dir: Temporary directory path
            error_type: Type of YAML error
                - 'indentation': Bad indentation
                - 'unclosed': Unclosed bracket
                - 'colon': Missing colon

        Returns:
            Absolute path to invalid file
        """
        invalid_contents = {
            'indentation': "model:\n  type: yolo_v8\n    path: bad  # Bad indent",
            'unclosed': "model:\n  type: [yolo_v8, yolov5",
            'colon': "model type yolo_v8  # Missing colon"
        }

        content = invalid_contents.get(error_type, invalid_contents['indentation'])

        invalid_file = tmp_dir / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write(content)

        return str(invalid_file)

    @staticmethod
    def create_profile_configs(tmp_dir: Path,
                               profiles: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Create multiple profile configuration files

        Args:
            tmp_dir: Temporary directory path
            profiles: List of profile names to create (default: ['dev', 'prod', 'testing'])

        Returns:
            Dictionary mapping profile names to file paths
        """
        if profiles is None:
            profiles = ['dev', 'prod', 'testing']

        profile_configs = {
            'dev': {
                'device': {'type': 'cpu'},
                'detection': {'confidence_threshold': 0.3},
                'logging': {'level': 'DEBUG'}
            },
            'prod': {
                'device': {'type': 'cuda'},
                'detection': {'confidence_threshold': 0.7},
                'logging': {'level': 'WARNING'}
            },
            'testing': {
                'device': {'type': 'cpu'},
                'detection': {'confidence_threshold': 0.5},
                'metrics': {'enabled': False}
            }
        }

        profile_paths = {}

        for profile in profiles:
            if profile not in profile_configs:
                continue

            profile_file = tmp_dir / f"{profile}.yaml"
            with open(profile_file, 'w') as f:
                yaml.dump(profile_configs[profile], f)

            profile_paths[profile] = str(profile_file)

        return profile_paths

    @staticmethod
    def _deep_merge(base: Dict[str, Any],
                   override: Dict[str, Any]) -> None:
        """
        Deep merge override dict into base dict (modifies base in place)

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigFactory._deep_merge(base[key], value)
            else:
                base[key] = value


class DetectionFactory:
    """
    Factory for creating detection results for testing
    """

    @staticmethod
    def create_detection(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a single detection result

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Detection dictionary with bbox, confidence, class_id, class_name
        """
        detection = {
            'bbox': [100, 100, 200, 200],
            'confidence': 0.85,
            'class_id': 0,
            'class_name': 'person'
        }

        if overrides:
            detection.update(overrides)

        return detection

    @staticmethod
    def create_detections(count: int = 5) -> List[Dict[str, Any]]:
        """
        Create multiple detection results

        Args:
            count: Number of detections to create

        Returns:
            List of detection dictionaries
        """
        class_names = ['person', 'car', 'dog', 'bicycle', 'motorcycle']

        detections = []
        for i in range(count):
            x1 = 50 + i * 100
            y1 = 50 + i * 50
            x2 = x1 + 100
            y2 = y1 + 100

            detection = {
                'bbox': [x1, y1, x2, y2],
                'confidence': max(0.5, 1.0 - i * 0.1),
                'class_id': i % len(class_names),
                'class_name': class_names[i % len(class_names)]
            }
            detections.append(detection)

        return detections

    @staticmethod
    def create_empty_detections() -> List[Dict[str, Any]]:
        """
        Create empty detection list

        Returns:
            Empty list
        """
        return []


class ImageFactory:
    """
    Factory for creating test images
    """

    @staticmethod
    def create_image(width: int = 640,
                    height: int = 480,
                    channels: int = 3) -> 'np.ndarray':
        """
        Create a test image with random values

        Args:
            width: Image width
            height: Image height
            channels: Number of channels (1=grayscale, 3=RGB/BGR)

        Returns:
            Numpy array representing image
        """
        import numpy as np

        if channels == 1:
            return np.random.randint(0, 255, (height, width), dtype=np.uint8)
        else:
            return np.random.randint(0, 255, (height, width, channels), dtype=np.uint8)

    @staticmethod
    def create_images_batch(count: int = 10,
                           width: int = 640,
                           height: int = 480) -> List:
        """
        Create a batch of test images

        Args:
            count: Number of images to create
            width: Image width
            height: Image height

        Returns:
            List of image numpy arrays
        """
        return [
            ImageFactory.create_image(width, height)
            for _ in range(count)
        ]

    @staticmethod
    def create_image_with_object(width: int = 640,
                                 height: int = 480,
                                 bbox: List[int] = None) -> 'np.ndarray':
        """
        Create test image with a visible object (white box)

        Args:
            width: Image width
            height: Image height
            bbox: Bounding box [x1, y1, x2, y2]

        Returns:
            Numpy array with white box at bbox location
        """
        import numpy as np

        image = np.zeros((height, width, 3), dtype=np.uint8)

        if bbox is None:
            bbox = [100, 100, 200, 200]

        x1, y1, x2, y2 = bbox
        image[y1:y2, x1:x2] = [255, 255, 255]  # White box

        return image


class ModelFactory:
    """
    Factory for creating mock YOLO models
    """

    @staticmethod
    def create_mock_yolo_result(num_detections: int = 2) -> 'Mock':
        """
        Create a mock YOLO result object

        Args:
            num_detections: Number of detections to include

        Returns:
            Mock result object
        """
        from unittest.mock import Mock
        import torch

        mock_result = Mock()
        mock_box = Mock()

        # Create mock tensors
        if num_detections > 0:
            bboxes = torch.tensor([[i * 100, i * 50, (i + 1) * 100, (i + 1) * 50]
                                  for i in range(num_detections)])
            confidences = torch.tensor([max(0.5, 1.0 - i * 0.1)
                                       for i in range(num_detections)])
            classes = torch.tensor([i % 3 for i in range(num_detections)])
        else:
            bboxes = torch.tensor([])
            confidences = torch.tensor([])
            classes = torch.tensor([])

        mock_box.xyxy = [bboxes]
        mock_box.conf = [confidences]
        mock_box.cls = [classes]

        mock_result.boxes = [mock_box] if num_detections > 0 else []
        mock_result.names = {0: "person", 1: "car", 2: "dog"}

        return mock_result

    @staticmethod
    def create_mock_yolo_model(num_detections: int = 2) -> 'Mock':
        """
        Create a mock YOLO model

        Args:
            num_detections: Number of detections to return

        Returns:
            Mock model object
        """
        from unittest.mock import Mock

        mock_result = ModelFactory.create_mock_yolo_result(num_detections)

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_model.names = {0: "person", 1: "car", 2: "dog"}

        return mock_model
