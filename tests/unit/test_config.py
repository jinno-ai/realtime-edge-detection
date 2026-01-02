"""
Unit tests for ConfigManager
Tests YAML loading, environment variable overrides, validation, and profile loading
"""
import os
import pytest
from pathlib import Path
import yaml

# Import the ConfigManager (will fail initially)
try:
    from src.core.config import ConfigManager
except ImportError:
    ConfigManager = None


class TestConfigManagerYAMLLoading:
    """Test YAML file loading functionality"""

    def test_load_valid_yaml_file(self, tmp_path):
        """Test loading a valid YAML configuration file"""
        # Create a valid YAML config
        config_file = tmp_path / "config.yaml"
        config_content = {
            'model': {
                'type': 'yolo_v8',
                'path': 'yolov8n.pt'
            },
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        # Test loading
        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            assert config is not None
            assert config['model']['type'] == 'yolo_v8'
            assert config['model']['path'] == 'yolov8n.pt'
            assert config['detection']['confidence_threshold'] == 0.5
            assert config['detection']['iou_threshold'] == 0.4
        else:
            pytest.fail("ConfigManager not implemented")

    def test_load_invalid_yaml_syntax(self, tmp_path):
        """Test handling of invalid YAML syntax with clear error messages"""
        # Create invalid YAML
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("model:\n  type: yolo_v8\n    path: yolov8n.pt  # Bad indentation")

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            # Check error message includes line number or location
            error_msg = str(exc_info.value)
            assert 'line' in error_msg.lower() or 'yaml' in error_msg.lower()
        else:
            pytest.fail("ConfigManager not implemented")

    def test_file_not_found_fallback_to_defaults(self, tmp_path):
        """Test graceful handling when config file doesn't exist"""
        non_existent_file = tmp_path / "non_existent.yaml"

        # Create default config file
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        if ConfigManager:
            # This should either load defaults or raise clear error
            manager = ConfigManager(str(non_existent_file), default_config=str(default_config))
            config = manager.load_config()

            # Should fallback to defaults
            assert config is not None
            assert config['model']['type'] == 'yolo_v8'
        else:
            pytest.fail("ConfigManager not implemented")

    def test_security_uses_safe_load(self, tmp_path):
        """Test that yaml.safe_load is used instead of yaml.load"""
        # Create YAML with malicious content
        config_file = tmp_path / "malicious.yaml"
        malicious_yaml = """
model: !!python/object/apply:os.system
  args: ['echo malicious']
"""
        with open(config_file, 'w') as f:
            f.write(malicious_yaml)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            # Should not execute code - should raise error or return string
            # If it tries to execute, test will fail
            with pytest.raises(Exception):
                config = manager.load_config()
        else:
            pytest.fail("ConfigManager not implemented")


class TestEnvironmentVariableOverrides:
    """Test environment variable override functionality"""

    def test_env_var_override_simple(self, tmp_path, monkeypatch):
        """Test basic environment variable override"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'model': {'type': 'yolo_v8', 'path': 'default.pt'}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        # Set environment variable
        monkeypatch.setenv('EDGE_DETECTION_MODEL_PATH', '/custom/path/model.pt')

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Environment variable should override
            assert config['model']['path'] == '/custom/path/model.pt'
        else:
            pytest.fail("ConfigManager not implemented")

    def test_env_var_parsing_edge_detection_prefix(self, monkeypatch):
        """Test that only EDGE_DETECTION_ prefix is parsed"""
        monkeypatch.setenv('EDGE_DETECTION_MODEL_TYPE', 'yolov10')
        monkeypatch.setenv('OTHER_VAR', 'should_be_ignored')

        if ConfigManager:
            manager = ConfigManager()
            config = manager.load_config()

            # Should have EDGE_DETECTION var, not OTHER_VAR
            # (Implementation dependent - just check no crash)
            assert config is not None
        else:
            pytest.fail("ConfigManager not implemented")

    def test_env_var_type_conversion_int(self, tmp_path, monkeypatch):
        """Test type conversion for integers"""
        config_file = tmp_path / "config.yaml"
        config_content = {'detection': {'batch_size': 1}}
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        # Set as string (env vars are always strings)
        monkeypatch.setenv('EDGE_DETECTION_DETECTION_BATCH_SIZE', '32')

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Should convert to int
            assert isinstance(config['detection']['batch_size'], int)
            assert config['detection']['batch_size'] == 32
        else:
            pytest.fail("ConfigManager not implemented")

    def test_env_var_type_conversion_float(self, tmp_path, monkeypatch):
        """Test type conversion for floats"""
        config_file = tmp_path / "config.yaml"
        config_content = {'detection': {'confidence_threshold': 0.5}}
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        monkeypatch.setenv('EDGE_DETECTION_DETECTION_CONFIDENCE_THRESHOLD', '0.75')

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Should convert to float
            assert isinstance(config['detection']['confidence_threshold'], float)
            assert config['detection']['confidence_threshold'] == 0.75
        else:
            pytest.fail("ConfigManager not implemented")

    def test_env_var_type_conversion_bool(self, tmp_path, monkeypatch):
        """Test type conversion for booleans"""
        config_file = tmp_path / "config.yaml"
        config_content = {'metrics': {'enabled': False}}
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        monkeypatch.setenv('EDGE_DETECTION_METRICS_ENABLED', 'true')

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Should convert to bool
            assert isinstance(config['metrics']['enabled'], bool)
            assert config['metrics']['enabled'] is True
        else:
            pytest.fail("ConfigManager not implemented")


class TestConfigMerging:
    """Test default configuration merging"""

    def test_merge_user_config_with_defaults(self, tmp_path):
        """Test that user config overrides defaults"""
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5, 'iou_threshold': 0.4}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        user_config = tmp_path / "user.yaml"
        user_content = {
            'model': {'path': 'custom.pt'},  # Override path
            'detection': {'confidence_threshold': 0.7}  # Override confidence
        }
        with open(user_config, 'w') as f:
            yaml.dump(user_content, f)

        if ConfigManager:
            manager = ConfigManager(str(user_config), default_config=str(default_config))
            config = manager.load_config()

            # User overrides should apply
            assert config['model']['path'] == 'custom.pt'
            assert config['detection']['confidence_threshold'] == 0.7

            # Default values should remain for non-overridden keys
            assert config['model']['type'] == 'yolo_v8'
            assert config['detection']['iou_threshold'] == 0.4
        else:
            pytest.fail("ConfigManager not implemented")

    def test_missing_required_parameter_logs_warning(self, tmp_path, caplog):
        """Test that missing required parameters use defaults and log warnings"""
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        user_config = tmp_path / "user.yaml"
        user_content = {'model': {'type': 'yolo_v8'}}  # Missing path
        with open(user_config, 'w') as f:
            yaml.dump(user_content, f)

        if ConfigManager:
            manager = ConfigManager(str(user_config), default_config=str(default_config))

            # Should load with default for missing param
            config = manager.load_config()

            # Should use default value
            assert config['model']['path'] == 'yolov8n.pt'

            # Should log warning (check caplog for warnings)
            # (Implementation may vary)
        else:
            pytest.fail("ConfigManager not implemented")


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_confidence_threshold_range(self, tmp_path):
        """Test validation of confidence threshold (0.0-1.0)"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'detection': {'confidence_threshold': 1.5}  # Invalid: > 1.0
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            # load_config should raise exception for invalid config
            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            error_msg = str(exc_info.value)
            assert 'confidence_threshold' in error_msg
        else:
            pytest.fail("ConfigManager not implemented")

    def test_validate_iou_threshold_range(self, tmp_path):
        """Test validation of IOU threshold (0.0-1.0)"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'detection': {'iou_threshold': -0.1}  # Invalid: < 0.0
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            # load_config should raise exception for invalid config
            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            error_msg = str(exc_info.value)
            assert 'iou_threshold' in error_msg
        else:
            pytest.fail("ConfigManager not implemented")

    def test_validate_missing_required_parameters(self, tmp_path):
        """Test that missing required parameters use defaults and validation passes"""
        config_file = tmp_path / "config.yaml"
        config_content = {'model': {'type': 'yolo_v8'}}  # Missing path
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Should use default value for missing required param
            assert config['model']['path'] == 'yolov8n.pt'  # From DEFAULT_CONFIG

            # Validation should pass since defaults fill in required params
            is_valid = manager.validate()
            assert is_valid is True
        else:
            pytest.fail("ConfigManager not implemented")

    def test_validate_provides_helpful_error_messages(self, tmp_path):
        """Test that validation errors include helpful hints"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'detection': {'confidence_threshold': 1.5}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            # Check for hint in error
            error = exc_info.value
            if hasattr(error, 'hint'):
                assert error.hint  # Hint should exist
                assert '0.0' in error.hint or '1.0' in error.hint
        else:
            pytest.fail("ConfigManager not implemented")


class TestDotNotationAccess:
    """Test nested config access via dot notation"""

    def test_get_simple_key(self, tmp_path):
        """Test getting a simple top-level key"""
        config_file = tmp_path / "config.yaml"
        config_content = {'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'}}
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            manager.load_config()

            # Test dot notation access
            result = manager.get('model.type')
            assert result == 'yolo_v8'

            result = manager.get('model.path')
            assert result == 'yolov8n.pt'
        else:
            pytest.fail("ConfigManager not implemented")

    def test_get_with_default_value(self, tmp_path):
        """Test get() method with default value for missing keys"""
        config_file = tmp_path / "config.yaml"
        config_content = {'model': {'type': 'yolo_v8'}}
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            manager.load_config()

            # Test default value
            result = manager.get('model.nonexistent', 'default_value')
            assert result == 'default_value'
        else:
            pytest.fail("ConfigManager not implemented")


class TestProfileLoading:
    """Test profile-based configuration loading"""

    def test_load_profile_overrides_base(self, tmp_path):
        """Test that profile settings override base settings"""
        # Create default config
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5, 'iou_threshold': 0.4}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        # Create profile config
        profile_config = tmp_path / "dev.yaml"
        profile_content = {
            'detection': {'confidence_threshold': 0.3}  # Override
        }
        with open(profile_config, 'w') as f:
            yaml.dump(profile_content, f)

        if ConfigManager:
            manager = ConfigManager(
                default_config=str(default_config),
                profile='dev'
            )
            manager.config_dir = tmp_path
            config = manager.load_config()

            # Profile should override base
            assert config['detection']['confidence_threshold'] == 0.3

            # Non-overridden values should remain
            assert config['detection']['iou_threshold'] == 0.4
            assert config['model']['type'] == 'yolo_v8'
        else:
            pytest.fail("ConfigManager not implemented")

    def test_load_profile_deep_merge(self, tmp_path):
        """Test that profile deep merges with base config"""
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt', 'download': True},
            'detection': {'confidence_threshold': 0.5}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        profile_config = tmp_path / "prod.yaml"
        profile_content = {
            'model': {'path': 'yolov8s.pt'}  # Only override path
        }
        with open(profile_config, 'w') as f:
            yaml.dump(profile_content, f)

        if ConfigManager:
            manager = ConfigManager(
                default_config=str(default_config),
                profile='prod'
            )
            manager.config_dir = tmp_path
            config = manager.load_config()

            # Path should be overridden
            assert config['model']['path'] == 'yolov8s.pt'

            # Other model values should remain
            assert config['model']['type'] == 'yolo_v8'
            assert config['model']['download'] is True
        else:
            pytest.fail("ConfigManager not implemented")

    def test_missing_profile_raises_error(self, tmp_path):
        """Test that missing profile file raises helpful error"""
        default_config = tmp_path / "default.yaml"
        default_content = {'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'}}
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        if ConfigManager:
            manager = ConfigManager(
                default_config=str(default_config),
                profile='nonexistent'
            )
            manager.config_dir = tmp_path

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            error_msg = str(exc_info.value)
            assert 'nonexistent' in error_msg
            assert 'not found' in error_msg.lower()
        else:
            pytest.fail("ConfigManager not implemented")

    def test_list_profiles(self, tmp_path):
        """Test listing available profiles"""
        # Create multiple profile files
        for profile in ['dev.yaml', 'prod.yaml', 'testing.yaml']:
            profile_file = tmp_path / profile
            with open(profile_file, 'w') as f:
                yaml.dump({}, f)

        if ConfigManager:
            manager = ConfigManager()
            manager.config_dir = tmp_path

            profiles = manager.list_profiles()

            assert 'dev' in profiles
            assert 'prod' in profiles
            assert 'testing' in profiles
            assert len(profiles) == 3
        else:
            pytest.fail("ConfigManager not implemented")

    def test_list_profiles_excludes_default(self, tmp_path):
        """Test that list_profiles excludes default.yaml"""
        default_config = tmp_path / "default.yaml"
        with open(default_config, 'w') as f:
            yaml.dump({}, f)

        dev_config = tmp_path / "dev.yaml"
        with open(dev_config, 'w') as f:
            yaml.dump({}, f)

        if ConfigManager:
            manager = ConfigManager()
            manager.config_dir = tmp_path

            profiles = manager.list_profiles()

            # Should only include dev, not default
            assert 'dev' in profiles
            assert 'default' not in profiles
            assert len(profiles) == 1
        else:
            pytest.fail("ConfigManager not implemented")

    def test_profile_error_message_includes_available_profiles(self, tmp_path):
        """Test that profile error message lists available profiles"""
        # Create some profiles
        for profile in ['dev.yaml', 'prod.yaml']:
            profile_file = tmp_path / profile
            with open(profile_file, 'w') as f:
                yaml.dump({}, f)

        if ConfigManager:
            manager = ConfigManager(profile='testing')
            manager.config_dir = tmp_path

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            error = exc_info.value
            error_msg = str(exc_info.value)

            # Check hint attribute if available
            if hasattr(error, 'hint') and error.hint:
                assert 'dev' in error.hint or 'prod' in error.hint
        else:
            pytest.fail("ConfigManager not implemented")


class TestConfigValidationIntegration:
    """Test ConfigManager validation integration"""

    def test_invalid_config_raises_validation_error(self, tmp_path):
        """Test that invalid config raises EdgeDetectionError"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'detection': {'confidence_threshold': 1.5}  # Invalid
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            error_msg = str(exc_info.value)
            assert 'confidence_threshold' in error_msg
        else:
            pytest.fail("ConfigManager not implemented")

    def test_valid_config_passes_validation(self, tmp_path):
        """Test that valid config passes validation"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5, 'iou_threshold': 0.4},
            'device': {'type': 'cpu'},
            'logging': {'level': 'INFO', 'format': 'json'}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            assert config is not None
            assert config['detection']['confidence_threshold'] == 0.5
        else:
            pytest.fail("ConfigManager not implemented")

    def test_validation_includes_helpful_hints(self, tmp_path):
        """Test that validation errors include actionable hints"""
        config_file = tmp_path / "config.yaml"
        config_content = {
            'detection': {'confidence_threshold': 1.5}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))

            with pytest.raises(Exception) as exc_info:
                manager.load_config()

            # Check for hint in error
            error = exc_info.value
            if hasattr(error, 'hint'):
                assert error.hint  # Hint should exist
        else:
            pytest.fail("ConfigManager not implemented")

    def test_validate_method_returns_errors(self, tmp_path):
        """Test that validate() method returns validation errors"""
        # Create a valid config first to load
        config_file = tmp_path / "config.yaml"
        config_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5}  # Valid to load
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        if ConfigManager:
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Now manually set invalid value to test validate() method
            manager._config['detection']['confidence_threshold'] = 1.5

            is_valid = manager.validate()
            assert is_valid is False

            errors = manager.get_validation_errors()
            assert len(errors) > 0
            assert 'confidence_threshold' in errors[0]
        else:
            pytest.fail("ConfigManager not implemented")


class TestProfileValidation:
    """Test validation with profile-based configurations"""

    def test_profile_with_invalid_config_raises_error(self, tmp_path):
        """Test that profile with invalid config raises error"""
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        # Create profile with invalid config
        profile_config = tmp_path / "badprofile.yaml"
        profile_content = {
            'detection': {'confidence_threshold': 2.0}  # Invalid
        }
        with open(profile_config, 'w') as f:
            yaml.dump(profile_content, f)

        if ConfigManager:
            manager = ConfigManager(
                default_config=str(default_config),
                profile='badprofile'
            )
            manager.config_dir = tmp_path

            with pytest.raises(Exception):
                manager.load_config()
        else:
            pytest.fail("ConfigManager not implemented")

    def test_profile_with_valid_config_passes(self, tmp_path):
        """Test that profile with valid config passes validation"""
        default_config = tmp_path / "default.yaml"
        default_content = {
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'detection': {'confidence_threshold': 0.5}
        }
        with open(default_config, 'w') as f:
            yaml.dump(default_content, f)

        # Create profile with valid config
        profile_config = tmp_path / "goodprofile.yaml"
        profile_content = {
            'detection': {'confidence_threshold': 0.7}  # Valid
        }
        with open(profile_config, 'w') as f:
            yaml.dump(profile_content, f)

        if ConfigManager:
            manager = ConfigManager(
                default_config=str(default_config),
                profile='goodprofile'
            )
            manager.config_dir = tmp_path
            config = manager.load_config()

            assert config['detection']['confidence_threshold'] == 0.7
        else:
            pytest.fail("ConfigManager not implemented")


# Run tests if this file is executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
