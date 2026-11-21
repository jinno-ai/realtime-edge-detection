"""
Unit tests for ConfigManager (src.core.config)

These tests exercise the actual ConfigManager contract:
- ConfigManager(config_path=..., profile=...) loads eagerly at construction
- get() uses dot-notation keys (e.g. 'detection.confidence_threshold')
- Invalid configuration raises EdgeDetectionError
- Missing config files fall back to defaults with a warning
"""

import pytest
import os
import tempfile
from pathlib import Path
import yaml

from src.core.config import ConfigManager
from src.core.errors import EdgeDetectionError


@pytest.fixture(autouse=True)
def clean_env():
    """Fixture to clean environment variables before and after each test"""
    # Save original env vars
    original_env = os.environ.copy()

    # Clear all EDGE_DETECTION_ env vars
    for key in list(os.environ.keys()):
        if key.startswith('EDGE_DETECTION_'):
            del os.environ[key]

    yield

    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)


class TestConfigManager:
    """Test suite for ConfigManager"""

    def test_default_config(self):
        """Test loading default configuration"""
        config = ConfigManager()

        assert config.get('model.path') == 'yolov8n.pt'
        assert config.get('detection.confidence_threshold') == 0.5
        assert config.get('detection.iou_threshold') == 0.4
        assert config.get('device.type') == 'auto'

    def test_config_from_file(self):
        """Test loading configuration from YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'model': {'path': 'custom_model.pt', 'auto_download': True},
                'detection': {'confidence_threshold': 0.7}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConfigManager(config_path=temp_path)

            assert config.get('model.path') == 'custom_model.pt'
            assert config.get('detection.confidence_threshold') == 0.7
            # Default value should be used for iou_threshold
            assert config.get('detection.iou_threshold') == 0.4
        finally:
            os.unlink(temp_path)

    def test_profile_config(self):
        """Test loading profile-specific configuration"""
        config = ConfigManager(profile='dev')

        # dev.yaml: lower threshold for debugging
        assert config.get('device.type') == 'auto'
        assert config.get('detection.confidence_threshold') == 0.25

    def test_env_override(self):
        """Test environment variable overrides"""
        # Set environment variables
        os.environ['EDGE_DETECTION_MODEL_PATH'] = 'env_model.pt'
        os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD'] = '0.8'

        try:
            config = ConfigManager()

            assert config.get('model.path') == 'env_model.pt'
            assert config.get('detection.confidence_threshold') == 0.8
        finally:
            # Clean up
            del os.environ['EDGE_DETECTION_MODEL_PATH']
            del os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD']

    def test_validation_confidence_range(self):
        """Test validation of confidence threshold range"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'confidence_threshold': 1.5}  # Invalid: > 1.0
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError, match="confidence_threshold"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_validation_iou_range(self):
        """Test validation of IOU threshold range"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'iou_threshold': -0.1}  # Invalid: < 0.0
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError, match="iou_threshold"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_validation_device_type(self):
        """Test validation of device type"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'device': {'type': 'invalid_device'}  # Invalid device type
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError, match="device"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_with_default(self):
        """Test get() method with default value"""
        config = ConfigManager()

        # Existing key
        assert config.get('model.path') == 'yolov8n.pt'

        # Non-existing key with default
        assert config.get('model.non_existing_key', 'default_value') == 'default_value'

    def test_get_missing_key_returns_none(self):
        """Test get() returns None for a non-existing key without default"""
        config = ConfigManager()

        assert config.get('model.non_existing_key') is None

    def test_get_section(self):
        """Test get() on a top-level section returns the nested dict"""
        config = ConfigManager()

        model_section = config.get('model')

        assert isinstance(model_section, dict)
        assert 'path' in model_section

    def test_get_non_existing_section(self):
        """Test get() on a non-existing section returns None"""
        config = ConfigManager()

        assert config.get('non_existing_section') is None

    def test_invalid_yaml(self):
        """Test loading invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:\n  - [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError, match="Invalid YAML"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_config_file_not_found_falls_back_to_defaults(self):
        """Test loading non-existent configuration file falls back to defaults"""
        config = ConfigManager(config_path='/non/existent/path/config.yaml')

        assert config.get('model.path') == 'yolov8n.pt'
        assert config.get('detection.confidence_threshold') == 0.5

    def test_env_override_parsing_bool(self):
        """Test environment variable parsing for boolean values"""
        os.environ['EDGE_DETECTION_MODEL_AUTO_DOWNLOAD'] = 'true'

        try:
            config = ConfigManager()
            assert config.get('model.auto_download') is True
        finally:
            del os.environ['EDGE_DETECTION_MODEL_AUTO_DOWNLOAD']

    def test_env_override_parsing_int(self):
        """Test environment variable parsing for integer values"""
        os.environ['EDGE_DETECTION_DETECTION_MAX_DETECTIONS'] = '50'

        try:
            config = ConfigManager()
            assert config.get('detection.max_detections') == 50
        finally:
            del os.environ['EDGE_DETECTION_DETECTION_MAX_DETECTIONS']

    def test_env_override_parsing_float(self):
        """Test environment variable parsing for float values"""
        os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD'] = '0.75'

        try:
            config = ConfigManager()
            assert config.get('detection.confidence_threshold') == 0.75
        finally:
            del os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD']

    def test_repr(self):
        """Test string representation"""
        config = ConfigManager()
        repr_str = repr(config)

        assert 'ConfigManager' in repr_str


class TestConfigValidationEnhanced:
    """Enhanced validation tests for Story 1.2"""

    def test_valid_configuration_passes_validation(self):
        """Test that a valid configuration passes all validation rules"""
        config = ConfigManager()
        # Should not raise any exception
        config._validate_configuration()

    def test_confidence_threshold_out_of_range_high(self):
        """Test confidence threshold > 1.0 shows clear error message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'confidence_threshold': 1.5}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'confidence_threshold' in error_msg
            assert '1.5' in error_msg or '1.50' in error_msg
            assert '0.0' in error_msg
            assert '1.0' in error_msg
        finally:
            os.unlink(temp_path)

    def test_confidence_threshold_out_of_range_low(self):
        """Test confidence threshold < 0.0 shows clear error message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'confidence_threshold': -0.1}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'confidence_threshold' in error_msg
            assert '0.0' in error_msg
        finally:
            os.unlink(temp_path)

    def test_iou_threshold_out_of_range_high(self):
        """Test IOU threshold > 1.0 shows clear error message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'iou_threshold': 1.2}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'iou_threshold' in error_msg
            assert '0.0' in error_msg
            assert '1.0' in error_msg
        finally:
            os.unlink(temp_path)

    def test_max_detections_out_of_range(self):
        """Test max_detections validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'max_detections': 0}  # Too low
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'max_detections' in error_msg
        finally:
            os.unlink(temp_path)

    def test_image_size_invalid_list_length(self):
        """Test input.image_size with invalid list length"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'input': {'image_size': [640]}  # Only 1 element
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'image_size' in error_msg
        finally:
            os.unlink(temp_path)

    def test_device_type_invalid_value(self):
        """Test invalid device type with helpful error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'device': {'type': 'invalid_device_type'},
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(EdgeDetectionError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'device.type' in error_msg or 'Device type' in error_msg
        finally:
            os.unlink(temp_path)

    def test_model_path_missing_uses_default(self):
        """Test that missing model.path falls back to the default"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'model': {}  # Missing path
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConfigManager(config_path=temp_path)
            # Implementation warns and fills the default rather than raising
            assert config.get('model.path') == 'yolov8n.pt'
        finally:
            os.unlink(temp_path)


class TestProfileLoading:
    """Profile loading tests for Story 1.2"""

    def test_load_profile_prod(self):
        """Test loading production profile"""
        config = ConfigManager(profile='prod')

        # Check prod-specific settings
        assert config.get('device.type') == 'auto'
        assert config.get('logging.level') == 'INFO'

    def test_load_profile_dev(self):
        """Test loading development profile"""
        config = ConfigManager(profile='dev')

        # Check dev-specific settings (config/dev.yaml)
        assert config.get('device.type') == 'auto'
        assert config.get('logging.level') == 'DEBUG'

    def test_load_profile_testing(self):
        """Test loading testing profile"""
        config = ConfigManager(profile='testing')

        # Check testing-specific settings (config/testing.yaml)
        assert config.get('device.type') == 'cpu'
        assert config.get('metrics.enabled') is True

    def test_profile_overrides_base_config(self):
        """Test that profile settings override base config"""
        config = ConfigManager(profile='dev')

        # dev.yaml lowers the threshold for debugging
        assert config.get('detection.confidence_threshold') == 0.25

    def test_missing_profile_error_message(self):
        """Test helpful error message when profile doesn't exist"""
        with pytest.raises(EdgeDetectionError) as exc_info:
            ConfigManager(profile='nonexistent_profile')

        error_msg = str(exc_info.value)
        assert 'nonexistent_profile' in error_msg
        # Should list available profiles
        assert ('dev' in error_msg or 'prod' in error_msg or 'testing' in error_msg)

    def test_list_available_profiles(self):
        """Test list_profiles() helper method"""
        config = ConfigManager()
        profiles = config.list_profiles()

        assert isinstance(profiles, list)
        # Should at least have the default profiles
        assert 'dev' in profiles
        assert 'prod' in profiles
        assert 'testing' in profiles
