"""
Unit tests for ConfigManager
"""

import pytest
import os
import tempfile
from pathlib import Path
import yaml

from src.core.config import ConfigManager


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

        assert config.get('model', 'path') == 'yolov8n.pt'
        assert config.get('detection', 'confidence_threshold') == 0.5
        assert config.get('detection', 'iou_threshold') == 0.4
        assert config.get('device', 'type') == 'auto'

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

            assert config.get('model', 'path') == 'custom_model.pt'
            assert config.get('detection', 'confidence_threshold') == 0.7
            # Default value should be used for iou_threshold
            assert config.get('detection', 'iou_threshold') == 0.4
        finally:
            os.unlink(temp_path)

    def test_profile_config(self):
        """Test loading profile-specific configuration"""
        config = ConfigManager(profile='dev')

        assert config.get('device', 'type') == 'cpu'
        assert config.get('detection', 'confidence_threshold') == 0.3

    def test_env_override(self):
        """Test environment variable overrides"""
        # Set environment variables
        os.environ['EDGE_DETECTION_MODEL_PATH'] = 'env_model.pt'
        os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD'] = '0.8'

        try:
            config = ConfigManager()

            assert config.get('model', 'path') == 'env_model.pt'
            assert config.get('detection', 'confidence_threshold') == 0.8
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
            with pytest.raises(ValueError, match="Configuration Validation Error"):
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
            with pytest.raises(ValueError, match="Configuration Validation Error"):
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
            with pytest.raises(ValueError, match="Configuration Validation Error"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_with_default(self):
        """Test get() method with default value"""
        config = ConfigManager()

        # Existing key
        assert config.get('model', 'path') == 'yolov8n.pt'

        # Non-existing key with default
        assert config.get('model', 'non_existing_key', default='default_value') == 'default_value'

    def test_get_with_default_raises_error(self):
        """Test get() method raises error for non-existing key without default"""
        config = ConfigManager()

        with pytest.raises(KeyError):
            config.get('model', 'non_existing_key')

    def test_get_section(self):
        """Test get_section() method"""
        config = ConfigManager()

        model_section = config.get_section('model')

        assert isinstance(model_section, dict)
        assert 'path' in model_section
        assert 'auto_download' in model_section

    def test_get_non_existing_section(self):
        """Test get_section() with non-existing section"""
        config = ConfigManager()

        with pytest.raises(KeyError):
            config.get_section('non_existing_section')

    def test_invalid_yaml(self):
        """Test loading invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:\n  - [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                ConfigManager(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_config_file_not_found(self):
        """Test loading non-existent configuration file"""
        with pytest.raises(FileNotFoundError):
            ConfigManager(config_path='/non/existent/path/config.yaml')

    def test_save_default_config(self):
        """Test saving default configuration to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_config.yaml'

            config = ConfigManager()
            config.save_default_config(str(output_path))

            assert output_path.exists()

            # Load saved config and verify
            with open(output_path, 'r') as f:
                saved_config = yaml.safe_load(f)

            assert saved_config['model']['path'] == 'yolov8n.pt'
            assert saved_config['detection']['confidence_threshold'] == 0.5

    def test_env_override_parsing_bool(self):
        """Test environment variable parsing for boolean values"""
        os.environ['EDGE_DETECTION_MODEL_AUTO_DOWNLOAD'] = 'true'

        try:
            config = ConfigManager()
            assert config.get('model', 'auto_download') is True
        finally:
            del os.environ['EDGE_DETECTION_MODEL_AUTO_DOWNLOAD']

    def test_env_override_parsing_int(self):
        """Test environment variable parsing for integer values"""
        os.environ['EDGE_DETECTION_DETECTION_MAX_DETECTIONS'] = '50'

        try:
            config = ConfigManager()
            assert config.get('detection', 'max_detections') == 50
        finally:
            del os.environ['EDGE_DETECTION_DETECTION_MAX_DETECTIONS']

    def test_env_override_parsing_float(self):
        """Test environment variable parsing for float values"""
        os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD'] = '0.75'

        try:
            config = ConfigManager()
            assert config.get('detection', 'confidence_threshold') == 0.75
        finally:
            del os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD']

    def test_to_dataclass(self):
        """Test converting configuration to Config dataclass"""
        config = ConfigManager()
        dataclass = config.to_dataclass()

        assert hasattr(dataclass, 'model')
        assert hasattr(dataclass, 'device')
        assert hasattr(dataclass, 'detection')
        assert hasattr(dataclass, 'preprocessing')
        assert hasattr(dataclass, 'output')

        assert dataclass.model['path'] == 'yolov8n.pt'

    def test_repr(self):
        """Test string representation"""
        config = ConfigManager()
        repr_str = repr(config)

        assert 'ConfigManager' in repr_str
        assert 'model' in repr_str
        assert 'device' in repr_str


class TestConfigValidationEnhanced:
    """Enhanced validation tests for Story 1.2"""

    def test_valid_configuration_passes_validation(self):
        """Test that a valid configuration passes all validation rules"""
        config = ConfigManager()
        # Should not raise any exception
        config._validate_config()

    def test_confidence_threshold_out_of_range_high(self):
        """Test confidence threshold > 1.0 shows clear error message"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'detection': {'confidence_threshold': 1.5}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
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
            with pytest.raises(ValueError) as exc_info:
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
            with pytest.raises(ValueError) as exc_info:
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
            with pytest.raises(ValueError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'max_detections' in error_msg
        finally:
            os.unlink(temp_path)

    def test_target_size_invalid_list_length(self):
        """Test target_size with invalid list length"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'preprocessing': {'target_size': [640]}  # Only 1 element
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'target_size' in error_msg
        finally:
            os.unlink(temp_path)

    def test_device_type_invalid_value(self):
        """Test invalid device type with helpful error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'device': {'type': 'invalid_device_type'},
                'preprocessing': {'target_size': [640, 640]},  # Valid to avoid other errors
                'detection': {'confidence_threshold': 0.5, 'iou_threshold': 0.4, 'max_detections': 100}
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            assert 'device.type' in error_msg or 'Device type' in error_msg
        finally:
            os.unlink(temp_path)

    def test_model_path_required_missing(self):
        """Test that model.path is required"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'model': {}  # Missing path
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ConfigManager(config_path=temp_path)

            error_msg = str(exc_info.value)
            # Should have some validation error
            assert len(error_msg) > 0
        finally:
            os.unlink(temp_path)


class TestProfileLoading:
    """Profile loading tests for Story 1.2"""

    def test_load_profile_prod(self):
        """Test loading production profile"""
        config = ConfigManager(profile='prod')

        # Check prod-specific settings
        assert config.get('device', 'type') == 'auto'
        assert config.get('logging', 'level') == 'INFO'

    def test_load_profile_dev(self):
        """Test loading development profile"""
        config = ConfigManager(profile='dev')

        # Check dev-specific settings
        assert config.get('device', 'type') == 'cpu'
        assert config.get('logging', 'level') == 'DEBUG'

    def test_load_profile_testing(self):
        """Test loading testing profile"""
        config = ConfigManager(profile='testing')

        # Check testing-specific settings
        assert config.get('device', 'type') == 'cpu'
        assert config.get('metrics', 'enabled') is False

    def test_profile_overrides_base_config(self):
        """Test that profile settings override base config"""
        config = ConfigManager(profile='dev')

        # dev.yaml should override confidence_threshold
        assert config.get('detection', 'confidence_threshold') == 0.3

    def test_missing_profile_error_message(self):
        """Test helpful error message when profile doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigManager(profile='nonexistent_profile')

        error_msg = str(exc_info.value)
        assert 'nonexistent_profile' in error_msg
        # Should list available profiles
        assert ('dev' in error_msg or 'prod' in error_msg or 'testing' in error_msg)

    def test_list_available_profiles(self):
        """Test _list_available_profiles helper method"""
        config = ConfigManager()
        profiles = config._list_available_profiles()

        assert isinstance(profiles, dict)
        # Should at least have the three default profiles
        assert 'dev' in profiles or 'prod' in profiles or 'testing' in profiles
        # Should have descriptions
        if 'dev' in profiles:
            assert 'debug logging' in profiles['dev'].lower()
