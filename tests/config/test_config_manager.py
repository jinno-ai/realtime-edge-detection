"""
Unit tests for ConfigManager.

Tests cover YAML loading, environment variable overrides, error handling,
and configuration validation.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.config.config_manager import ConfigManager, ConfigurationError


class TestConfigManagerBasics:
    """Test basic ConfigManager functionality."""

    def test_load_defaults_only(self):
        """Test loading with default configuration only."""
        config = ConfigManager()
        config.load()

        assert config.get('model.name') == 'yolov8n'
        assert config.get('detection.confidence_threshold') == 0.25
        assert config.get('device.type') == 'auto'

    def test_get_with_default(self):
        """Test get() with default value for missing key."""
        config = ConfigManager()
        config.load()

        result = config.get('nonexistent.key', 'default_value')
        assert result == 'default_value'

    def test_get_nested_value(self):
        """Test accessing nested configuration values."""
        config = ConfigManager()
        config.load()

        assert config.get('model.cache_dir') is not None
        assert config.get('detection.iou_threshold') == 0.45

    def test_get_all(self):
        """Test getting complete configuration."""
        config = ConfigManager()
        config.load()

        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert 'model' in all_config
        assert 'detection' in all_config
        assert 'device' in all_config

    def test_get_without_loading(self):
        """Test that get() raises error before load()."""
        config = ConfigManager()

        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            config.get('model.name')


class TestYAMLLoading:
    """Test YAML file loading."""

    def test_load_valid_yaml(self):
        """Test loading a valid YAML configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {'name': 'yolov8s'},
                'detection': {'confidence_threshold': 0.5}
            }, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            assert config.get('model.name') == 'yolov8s'
            assert config.get('detection.confidence_threshold') == 0.5
        finally:
            os.unlink(temp_path)

    def test_yaml_merges_with_defaults(self):
        """Test that YAML config merges with defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'model': {'name': 'yolov8m'}}, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Overridden value
            assert config.get('model.name') == 'yolov8m'
            # Default value still present
            assert config.get('detection.confidence_threshold') == 0.25
        finally:
            os.unlink(temp_path)

    def test_invalid_yaml_syntax(self):
        """Test error handling for invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("model:\n  name: yolov8n\n  bad_indent: bad\n    value\n")
            temp_path = f.name

        try:
            config = ConfigManager()
            with pytest.raises(ConfigurationError, match="Invalid YAML syntax"):
                config.load(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_yaml_file(self):
        """Test loading an empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)
            # Should load defaults
            assert config.get('model.name') == 'yolov8n'
        finally:
            os.unlink(temp_path)

    def test_nonexistent_yaml_path(self):
        """Test loading from non-existent path (should use defaults)."""
        config = ConfigManager()
        config.load('/nonexistent/path/config.yaml')

        # Should load defaults without error
        assert config.get('model.name') == 'yolov8n'


class TestEnvironmentVariables:
    """Test environment variable configuration overrides."""

    def test_env_override_string(self):
        """Test string environment variable override."""
        os.environ['EDGE_DETECTION_MODEL__NAME'] = 'yolov8x'

        try:
            config = ConfigManager()
            config.load()

            assert config.get('model.name') == 'yolov8x'
        finally:
            del os.environ['EDGE_DETECTION_MODEL__NAME']

    def test_env_override_int(self):
        """Test integer type conversion from env var."""
        os.environ['EDGE_DETECTION_DETECTION__MAX_DETECTIONS'] = '500'

        try:
            config = ConfigManager()
            config.load()

            assert config.get('detection.max_detections') == 500
        finally:
            del os.environ['EDGE_DETECTION_DETECTION__MAX_DETECTIONS']

    def test_env_override_float(self):
        """Test float type conversion from env var."""
        os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD'] = '0.75'

        try:
            config = ConfigManager()
            config.load()

            assert config.get('detection.confidence_threshold') == 0.75
        finally:
            del os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD']

    def test_env_override_bool(self):
        """Test boolean type conversion from env var."""
        os.environ['EDGE_DETECTION_PERFORMANCE__HALF_PRECISION'] = 'true'

        try:
            config = ConfigManager()
            config.load()

            assert config.get('performance.half_precision') is True
        finally:
            del os.environ['EDGE_DETECTION_PERFORMANCE__HALF_PRECISION']

    def test_env_priority_over_yaml(self):
        """Test that env vars override YAML values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'model': {'name': 'yolov8s'}}, f)
            temp_path = f.name

        os.environ['EDGE_DETECTION_MODEL__NAME'] = 'yolov8l'

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Env var should override YAML
            assert config.get('model.name') == 'yolov8l'
        finally:
            os.unlink(temp_path)
            del os.environ['EDGE_DETECTION_MODEL__NAME']


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_valid_configuration(self):
        """Test validation passes for valid configuration."""
        config = ConfigManager()
        config.load()

        assert config.validate() is True

    def test_invalid_confidence_threshold(self):
        """Test validation fails for invalid confidence threshold."""
        os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD'] = '1.5'

        try:
            config = ConfigManager()
            config.load()

            with pytest.raises(ConfigurationError, match="Invalid confidence_threshold"):
                config.validate()
        finally:
            del os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD']

    def test_invalid_iou_threshold(self):
        """Test validation fails for invalid IOU threshold."""
        os.environ['EDGE_DETECTION_DETECTION__IOU_THRESHOLD'] = '-0.1'

        try:
            config = ConfigManager()
            config.load()

            with pytest.raises(ConfigurationError, match="Invalid iou_threshold"):
                config.validate()
        finally:
            del os.environ['EDGE_DETECTION_DETECTION__IOU_THRESHOLD']

    def test_invalid_device_type(self):
        """Test validation fails for invalid device type."""
        os.environ['EDGE_DETECTION_DEVICE__TYPE'] = 'invalid_device'

        try:
            config = ConfigManager()
            config.load()

            with pytest.raises(ConfigurationError, match="Invalid device type"):
                config.validate()
        finally:
            del os.environ['EDGE_DETECTION_DEVICE__TYPE']

    def test_validate_without_loading(self):
        """Test that validate() raises error before load()."""
        config = ConfigManager()

        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            config.validate()


class TestConfigurationMerge:
    """Test configuration merging behavior."""

    def test_nested_merge(self):
        """Test deep merging of nested dictionaries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {'name': 'yolov8s', 'cache_dir': '/custom/cache'},
                'detection': {'confidence_threshold': 0.5}
            }, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Custom values
            assert config.get('model.name') == 'yolov8s'
            assert config.get('model.cache_dir') == '/custom/cache'
            assert config.get('detection.confidence_threshold') == 0.5

            # Default values preserved
            assert config.get('detection.iou_threshold') == 0.45
        finally:
            os.unlink(temp_path)
