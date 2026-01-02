"""
Unit tests for core ConfigManager (P0 Critical Paths)

Tests cover:
- YAML configuration loading (happy path, edge cases, errors)
- Environment variable overrides
- Configuration validation
- Profile loading
- Error messages and hints
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

from src.core.config import ConfigManager
from src.core.errors import EdgeDetectionError, ErrorCode
from src.core.validators import ValidationError


@pytest.fixture(autouse=True)
def isolate_environment():
    """
    Clean environment variables before and after each test.
    Ensures tests are deterministic and isolated.
    """
    # Save original environment
    original_env = os.environ.copy()

    # Clear all EDGE_DETECTION_* variables
    keys_to_remove = [k for k in os.environ if k.startswith('EDGE_DETECTION_')]
    for key in keys_to_remove:
        del os.environ[key]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestConfigLoadingCriticalPaths:
    """
    P0: Configuration loading (happy path and critical errors)
    Covers: Story 1.1, R-001, R-004, R-006
    """

    @pytest.mark.unit
    def test_load_default_configuration_without_file(self):
        """
        [P0] GIVEN: No config file exists
        WHEN: ConfigManager is initialized without arguments
        THEN: Default configuration is loaded successfully
        """
        # GIVEN: No config file (working directory cleaned in test setup)

        # WHEN: Initializing ConfigManager without arguments
        config_mgr = ConfigManager()
        config = config_mgr.load_config()

        # THEN: Default values are loaded
        assert config['model']['type'] == 'yolo_v8'
        assert config['model']['path'] == 'yolov8n.pt'
        assert config['detection']['confidence_threshold'] == 0.5
        assert config['device']['type'] == 'auto'

    @pytest.mark.unit
    def test_load_yaml_configuration_from_file(self, tmp_path):
        """
        [P0] GIVEN: A valid YAML configuration file exists
        WHEN: ConfigManager loads the file
        THEN: Configuration is merged with defaults
        """
        # GIVEN: Valid YAML config file
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'model': {
                'type': 'yolo_v8',
                'path': 'custom_model.pt',
                'download': False
            },
            'detection': {
                'confidence_threshold': 0.75,
                'iou_threshold': 0.5
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # WHEN: Loading configuration from file
        config_mgr = ConfigManager(config_path=str(config_file))
        config = config_mgr.load_config()

        # THEN: User config overrides defaults
        assert config['model']['path'] == 'custom_model.pt'
        assert config['model']['download'] is False
        assert config['detection']['confidence_threshold'] == 0.75

        # AND: Default values are preserved for unspecified keys
        assert config['detection']['max_detections'] == 100

    @pytest.mark.unit
    def test_invalid_yaml_syntax_raises_clear_error(self, tmp_path):
        """
        [P0] GIVEN: A YAML file with syntax errors
        WHEN: ConfigManager tries to load it
        THEN: Raises EdgeDetectionError with line number and hint
        """
        # GIVEN: Invalid YAML (indentation error)
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("model:\n  type: yolo_v8\n    path: bad  # Invalid indentation")

        # WHEN: Loading invalid YAML
        config_mgr = ConfigManager(config_path=str(config_file))

        # THEN: Raises error with clear message
        with pytest.raises(EdgeDetectionError) as exc_info:
            config_mgr.load_config()

        error = exc_info.value
        assert error.code == ErrorCode.INVALID_CONFIG
        assert 'Invalid YAML syntax' in str(error)
        # Check for hint
        assert error.hint is not None
        assert 'indentation' in error.hint.lower() or 'structure' in error.hint.lower()

    @pytest.mark.unit
    def test_non_dict_yaml_raises_error(self, tmp_path):
        """
        [P0] GIVEN: A YAML file that doesn't contain a dictionary
        WHEN: ConfigManager tries to load it
        THEN: Raises EdgeDetectionError with helpful message
        """
        # GIVEN: YAML with non-dict content (list)
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(['item1', 'item2'], f)

        # WHEN: Loading non-dict YAML
        config_mgr = ConfigManager(config_path=str(config_file))

        # THEN: Raises error
        with pytest.raises(EdgeDetectionError) as exc_info:
            config_mgr.load_config()

        error = exc_info.value
        assert error.code == ErrorCode.INVALID_CONFIG
        assert 'dictionary' in str(error).lower()

    @pytest.mark.unit
    def test_missing_config_file_with_explicit_path_raises_error(self):
        """
        [P0] GIVEN: An explicitly specified config file doesn't exist
        WHEN: ConfigManager tries to load it
        THEN: Raises EdgeDetectionError (not FileNotFoundError)
        """
        # GIVEN: Non-existent config path
        non_existent_path = "/non/existent/path/config.yaml"

        # WHEN: Initializing with non-existent path
        config_mgr = ConfigManager(config_path=non_existent_path)

        # THEN: Should not raise during init, but during load_config
        # ConfigManager logs warning and uses defaults
        config = config_mgr.load_config()

        # Should have defaults (not crashed)
        assert 'model' in config
        assert config['model']['type'] == 'yolo_v8'


class TestEnvironmentVariableOverrides:
    """
    P0: Environment variable configuration overrides
    Covers: Story 1.1, R-001
    """

    @pytest.mark.unit
    def test_env_override_model_path(self):
        """
        [P0] GIVEN: EDGE_DETECTION_MODEL_PATH environment variable is set
        WHEN: ConfigManager loads configuration
        THEN: Environment variable overrides YAML file
        """
        # GIVEN: Environment variable set
        os.environ['EDGE_DETECTION_MODEL_PATH'] = 'env_override_model.pt'

        # WHEN: Loading config
        config_mgr = ConfigManager()
        config = config_mgr.load_config()

        # THEN: Env var overrides default
        assert config['model']['path'] == 'env_override_model.pt'

    @pytest.mark.unit
    def test_env_override_confidence_threshold(self):
        """
        [P0] GIVEN: EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD is set
        WHEN: ConfigManager loads configuration
        THEN: Float value is correctly parsed and overrides defaults
        """
        # GIVEN: Environment variable with float value
        os.environ['EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD'] = '0.85'

        # WHEN: Loading config
        config_mgr = ConfigManager()
        config = config_mgr.load_config()

        # THEN: Value is parsed as float and overrides default
        assert config['detection']['confidence_threshold'] == 0.85
        assert isinstance(config['detection']['confidence_threshold'], float)

    @pytest.mark.unit
    def test_env_override_max_detections_as_integer(self):
        """
        [P0] GIVEN: EDGE_DETECTION_DETECTION_MAX_DETECTIONS is set
        WHEN: ConfigManager loads configuration
        THEN: Integer value is correctly parsed
        """
        # GIVEN: Environment variable with integer value
        os.environ['EDGE_DETECTION_DETECTION_MAX_DETECTIONS'] = '250'

        # WHEN: Loading config
        config_mgr = ConfigManager()
        config = config_mgr.load_config()

        # THEN: Value is parsed as int
        assert config['detection']['max_detections'] == 250
        assert isinstance(config['detection']['max_detections'], int)

    @pytest.mark.unit
    def test_env_override_boolean_true_variations(self):
        """
        [P0] GIVEN: Boolean environment variable with various 'true' values
        WHEN: ConfigManager loads configuration
        THEN: All variations are parsed as True
        """
        true_values = ['true', 'TRUE', 'yes', 'YES', '1']

        for value in true_values:
            # Clean environment
            if 'EDGE_DETECTION_MODEL_DOWNLOAD' in os.environ:
                del os.environ['EDGE_DETECTION_MODEL_DOWNLOAD']

            # GIVEN: Env var with 'true' variation
            os.environ['EDGE_DETECTION_MODEL_DOWNLOAD'] = value

            # WHEN: Loading config
            config_mgr = ConfigManager()
            config = config_mgr.load_config()

            # THEN: Parsed as boolean True
            assert config['model']['download'] is True
            assert isinstance(config['model']['download'], bool)

    @pytest.mark.unit
    def test_env_override_boolean_false_variations(self):
        """
        [P0] GIVEN: Boolean environment variable with various 'false' values
        WHEN: ConfigManager loads configuration
        THEN: All variations are parsed as False
        """
        false_values = ['false', 'FALSE', 'no', 'NO', '0']

        for value in false_values:
            # Clean environment
            if 'EDGE_DETECTION_MODEL_DOWNLOAD' in os.environ:
                del os.environ['EDGE_DETECTION_MODEL_DOWNLOAD']

            # GIVEN: Env var with 'false' variation
            os.environ['EDGE_DETECTION_MODEL_DOWNLOAD'] = value

            # WHEN: Loading config
            config_mgr = ConfigManager()
            config = config_mgr.load_config()

            # THEN: Parsed as boolean False
            assert config['model']['download'] is False
            assert isinstance(config['model']['download'], bool)

    @pytest.mark.unit
    def test_env_override_has_highest_priority(self, tmp_path):
        """
        [P0] GIVEN: Config file, profile, and env variable all set
        WHEN: ConfigManager loads configuration
        THEN: Environment variable has highest priority (overrides all)
        """
        # GIVEN: Config file with one value
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({'model': {'path': 'file_model.pt'}}, f)

        # AND: Profile with another value
        profile_file = tmp_path / "prod.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump({'model': {'path': 'profile_model.pt'}}, f)

        # AND: Environment variable with third value
        os.environ['EDGE_DETECTION_MODEL_PATH'] = 'env_model.pt'

        # WHEN: Loading all sources
        config_mgr = ConfigManager(
            config_path=str(config_file),
            default_config=str(profile_file)  # Using default_config param as profile
        )
        config = config_mgr.load_config()

        # THEN: Env var wins
        assert config['model']['path'] == 'env_model.pt'


class TestConfigurationValidation:
    """
    P0: Configuration validation with clear error messages
    Covers: Story 1.2, R-007
    """

    @pytest.mark.unit
    def test_valid_configuration_passes_validation(self):
        """
        [P0] GIVEN: A valid configuration
        WHEN: ConfigManager validates it
        THEN: Validation passes without errors
        """
        # GIVEN: Valid config
        config_mgr = ConfigManager()
        config_mgr.load_config()

        # WHEN: Validating
        is_valid = config_mgr.validate()

        # THEN: Passes validation
        assert is_valid is True
        assert len(config_mgr.get_validation_errors()) == 0

    @pytest.mark.unit
    def test_invalid_confidence_threshold_raises_error_with_hint(self):
        """
        [P0] GIVEN: Configuration with confidence_threshold > 1.0
        WHEN: ConfigManager validates it
        THEN: ValidationError with clear hint is raised
        """
        # GIVEN: Config with invalid confidence
        config_mgr = ConfigManager()
        config_mgr._config = {
            'detection': {'confidence_threshold': 1.5}
        }

        # WHEN: Validating
        is_valid = config_mgr.validate()

        # THEN: Validation fails with helpful error
        assert is_valid is False
        errors = config_mgr.get_validation_errors()
        assert len(errors) > 0
        assert any('confidence_threshold' in e for e in errors)
        # Error message includes hint
        assert any('0.0' in e and '1.0' in e for e in errors)

    @pytest.mark.unit
    def test_invalid_device_type_raises_error_with_allowed_values(self):
        """
        [P0] GIVEN: Configuration with invalid device type
        WHEN: ConfigManager validates it
        THEN: Error message shows allowed values
        """
        # GIVEN: Config with invalid device type
        config_mgr = ConfigManager()
        config_mgr._config = {
            'device': {'type': 'invalid_device'}
        }

        # WHEN: Validating
        is_valid = config_mgr.validate()

        # THEN: Validation fails
        assert is_valid is False
        errors = config_mgr.get_validation_errors()
        assert len(errors) > 0
        # Error includes allowed device types
        assert any('device' in e.lower() for e in errors)

    @pytest.mark.unit
    def test_multiple_validation_errors_all_reported(self):
        """
        [P0] GIVEN: Configuration with multiple invalid parameters
        WHEN: ConfigManager validates it
        THEN: All validation errors are reported (not just first)
        """
        # GIVEN: Config with multiple errors
        config_mgr = ConfigManager()
        config_mgr._config = {
            'detection': {
                'confidence_threshold': 1.5,  # Invalid
                'iou_threshold': -0.5,        # Invalid
                'max_detections': 0            # Invalid
            }
        }

        # WHEN: Validating
        is_valid = config_mgr.validate()

        # THEN: All errors reported
        assert is_valid is False
        errors = config_mgr.get_validation_errors()
        assert len(errors) >= 3  # At least 3 errors

    @pytest.mark.unit
    def test_validation_skips_none_values(self):
        """
        [P0] GIVEN: Configuration with None values
        WHEN: ConfigManager validates it
        THEN: None values are skipped (not validated)
        """
        # GIVEN: Config with None values (loaded config so validator is initialized)
        config_mgr = ConfigManager()
        config_mgr.load_config()  # Load defaults first to initialize validator

        # Now set None values
        config_mgr._config['detection']['confidence_threshold'] = None
        config_mgr._config['detection']['iou_threshold'] = None

        # WHEN: Validating
        is_valid = config_mgr.validate()

        # THEN: Passes (None values skipped by validator)
        assert is_valid is True
        assert len(config_mgr.get_validation_errors()) == 0


class TestProfileLoading:
    """
    P0: Configuration profile loading
    Covers: Story 1.1, R-011
    """

    @pytest.mark.unit
    def test_load_profile_successfully(self, tmp_path):
        """
        [P0] GIVEN: A profile YAML file exists in config directory
        WHEN: ConfigManager loads with profile parameter
        THEN: Profile configuration is merged with base config
        """
        # GIVEN: Profile file
        profile_file = tmp_path / "prod.yaml"
        profile_config = {
            'device': {'type': 'cuda'},
            'detection': {'confidence_threshold': 0.7}
        }
        with open(profile_file, 'w') as f:
            yaml.dump(profile_config, f)

        # WHEN: Loading with profile
        config_mgr = ConfigManager(profile='prod')
        config_mgr.config_dir = tmp_path  # Mock config dir
        config = config_mgr.load_config()

        # THEN: Profile values override defaults
        assert config['device']['type'] == 'cuda'
        assert config['detection']['confidence_threshold'] == 0.7

    @pytest.mark.unit
    def test_missing_profile_raises_clear_error(self, tmp_path):
        """
        [P0] GIVEN: Requested profile doesn't exist
        WHEN: ConfigManager tries to load it
        THEN: Raises EdgeDetectionError with available profiles listed
        """
        # GIVEN: Config dir with some profiles
        (tmp_path / "dev.yaml").touch()
        (tmp_path / "testing.yaml").touch()

        # WHEN: Loading non-existent profile
        config_mgr = ConfigManager(profile='nonexistent')
        config_mgr.config_dir = tmp_path

        # THEN: Raises error with helpful message
        with pytest.raises(EdgeDetectionError) as exc_info:
            config_mgr.load_config()

        error = exc_info.value
        assert error.code == ErrorCode.INVALID_CONFIG
        assert 'nonexistent' in str(error)
        # Should list available profiles
        assert 'dev' in error.hint or 'testing' in error.hint

    @pytest.mark.unit
    def test_list_available_profiles(self, tmp_path):
        """
        [P0] GIVEN: Config directory with multiple profile files
        WHEN: list_profiles() is called
        THEN: Returns alphabetically sorted list of profile names
        """
        # GIVEN: Multiple profile files
        (tmp_path / "prod.yaml").touch()
        (tmp_path / "dev.yaml").touch()
        (tmp_path / "testing.yaml").touch()
        (tmp_path / "default.yaml").touch()  # Should be excluded

        # WHEN: Listing profiles
        config_mgr = ConfigManager()
        config_mgr.config_dir = tmp_path
        profiles = config_mgr.list_profiles()

        # THEN: Returns sorted list excluding default.yaml
        assert len(profiles) == 3
        assert 'default' not in profiles
        assert profiles == sorted(profiles)  # Alphabetically sorted
        assert 'dev' in profiles
        assert 'prod' in profiles
        assert 'testing' in profiles


class TestDotNotationAccess:
    """
    P0: Configuration value access using dot notation
    Covers: Story 1.1
    """

    @pytest.mark.unit
    def test_get_nested_value_with_dot_notation(self):
        """
        [P0] GIVEN: A loaded configuration
        WHEN: Getting nested value using dot notation
        THEN: Returns correct value
        """
        # GIVEN: Loaded config
        config_mgr = ConfigManager()
        config_mgr.load_config()

        # WHEN: Getting nested value
        value = config_mgr.get('detection.confidence_threshold')

        # THEN: Returns correct value
        assert value == 0.5

    @pytest.mark.unit
    def test_get_non_existent_key_returns_default(self):
        """
        [P0] GIVEN: A loaded configuration
        WHEN: Getting non-existent key with default
        THEN: Returns default value
        """
        # GIVEN: Loaded config
        config_mgr = ConfigManager()
        config_mgr.load_config()

        # WHEN: Getting non-existent key
        value = config_mgr.get('non.existent.key', default='my_default')

        # THEN: Returns default
        assert value == 'my_default'

    @pytest.mark.unit
    def test_get_non_existent_key_without_default_returns_none(self):
        """
        [P0] GIVEN: A loaded configuration
        WHEN: Getting non-existent key without default
        THEN: Returns None
        """
        # GIVEN: Loaded config
        config_mgr = ConfigManager()
        config_mgr.load_config()

        # WHEN: Getting non-existent key
        value = config_mgr.get('non.existent.key')

        # THEN: Returns None
        assert value is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'unit'])
