"""
Integration tests for ConfigManager.

Tests real-world scenarios including file system operations,
configuration priority, and edge cases.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.config.config_manager import ConfigManager, ConfigurationError


class TestConfigPriority:
    """Test configuration loading priority: env vars > yaml > defaults."""

    def test_full_priority_chain(self):
        """Test that env vars > user yaml > project yaml > defaults."""
        # Create project config
        project_dir = Path('./config')
        project_dir.mkdir(exist_ok=True)
        project_config = project_dir / 'config.yaml'

        with open(project_config, 'w') as f:
            yaml.dump({
                'model': {'name': 'yolov8s', 'path': '/project/model.pt'},
                'detection': {'confidence_threshold': 0.4}
            }, f)

        # Create user config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {'name': 'yolov8m'},
                'detection': {'iou_threshold': 0.5}
            }, f)
            user_config_path = f.name

        # Set environment variable
        os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD'] = '0.7'

        try:
            config = ConfigManager()
            config.load(user_config_path)

            # Env var overrides everything
            assert config.get('detection.confidence_threshold') == 0.7

            # User config overrides project config
            assert config.get('model.name') == 'yolov8m'

            # Project config overrides defaults
            assert config.get('model.path') == '/project/model.pt'

            # User config specific value
            assert config.get('detection.iou_threshold') == 0.5

            # Default value (not overridden anywhere)
            assert config.get('device.type') == 'auto'
        finally:
            os.unlink(user_config_path)
            project_config.unlink()
            del os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD']


class TestFileSystemOperations:
    """Test file system related operations."""

    def test_load_from_user_config_directory(self, tmp_path):
        """Test loading from user config directory (~/.config/edge-detection/)."""
        config_dir = tmp_path / 'edge-detection'
        config_dir.mkdir()
        config_file = config_dir / 'config.yaml'

        with open(config_file, 'w') as f:
            yaml.dump({'model': {'name': 'yolov8l'}}, f)

        # Monkey patch the default config path
        from src.config import config_manager
        original_path = config_manager.get_default_config_path
        config_manager.get_default_config_path = lambda: tmp_path

        try:
            config = ConfigManager()
            config.load()

            assert config.get('model.name') == 'yolov8l'
        finally:
            config_manager.get_default_config_path = original_path

    def test_create_config_directory_if_not_exists(self, tmp_path):
        """Test that ConfigManager handles missing config directory gracefully."""
        nonexistent_config = tmp_path / 'nonexistent' / 'config.yaml'

        config = ConfigManager()
        # Should not raise error, just use defaults
        config.load(str(nonexistent_config))

        assert config.get('model.name') == 'yolov8n'

    def test_custom_config_path_argument(self):
        """Test loading config from custom path specified as argument."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {'name': 'custom_model'},
                'device': {'type': 'cpu'}
            }, f)
            custom_path = f.name

        try:
            config = ConfigManager()
            config.load(custom_path)

            assert config.get('model.name') == 'custom_model'
            assert config.get('device.type') == 'cpu'
        finally:
            os.unlink(custom_path)


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_yaml_with_comments(self):
        """Test that YAML comments are properly ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
# This is a comment
model:
  name: yolov8s  # Inline comment
  # Another comment
  path: /path/to/model.pt
detection:
  confidence_threshold: 0.5
""")
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            assert config.get('model.name') == 'yolov8s'
            assert config.get('model.path') == '/path/to/model.pt'
            assert config.get('detection.confidence_threshold') == 0.5
        finally:
            os.unlink(temp_path)

    def test_empty_sections_in_yaml(self):
        """Test YAML with empty sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {},  # Empty section
                'detection': {'confidence_threshold': 0.6}
            }, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Empty section should use defaults
            assert config.get('model.name') == 'yolov8n'
            # Override should work
            assert config.get('detection.confidence_threshold') == 0.6
        finally:
            os.unlink(temp_path)

    def test_multiple_config_loads(self):
        """Test that configuration can be reloaded."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'model': {'name': 'yolov8s'}}, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)
            assert config.get('model.name') == 'yolov8s'

            # Reload with different config
            with open(temp_path, 'w') as f:
                yaml.dump({'model': {'name': 'yolov8m'}}, f)

            config.load(temp_path)
            assert config.get('model.name') == 'yolov8m'
        finally:
            os.unlink(temp_path)

    def test_special_characters_in_strings(self):
        """Test handling of special characters in configuration strings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'output': {'save_dir': '/path/with spaces/output'},
                'logging': {'file': '/path/with-dashes/log.txt'}
            }, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            assert config.get('output.save_dir') == '/path/with spaces/output'
            assert config.get('logging.file') == '/path/with-dashes/log.txt'
        finally:
            os.unlink(temp_path)


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_production_config_with_overrides(self):
        """Simulate production deployment with environment-specific overrides."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'model': {'name': 'yolov8m', 'cache_dir': '/cache/models'},
                'device': {'type': 'cuda'},
                'output': {'save_dir': '/output'}
            }, f)
            temp_path = f.name

        # Production-specific overrides via env vars
        os.environ['EDGE_DETECTION_MODEL__NAME'] = 'yolov8l'
        os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD'] = '0.3'
        os.environ['EDGE_DETECTION_PERFORMANCE__HALF_PRECISION'] = 'true'

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Verify production settings
            assert config.get('model.name') == 'yolov8l'
            assert config.get('model.cache_dir') == '/cache/models'
            assert config.get('device.type') == 'cuda'
            assert config.get('output.save_dir') == '/output'
            assert config.get('detection.confidence_threshold') == 0.3
            assert config.get('performance.half_precision') is True

            # Should pass validation
            assert config.validate() is True
        finally:
            os.unlink(temp_path)
            del os.environ['EDGE_DETECTION_MODEL__NAME']
            del os.environ['EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD']
            del os.environ['EDGE_DETECTION_PERFORMANCE__HALF_PRECISION']

    def test_development_config(self):
        """Simulate development configuration with debugging enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'logging': {'level': 'DEBUG', 'format': 'text'},
                'device': {'type': 'cpu'},
                'detection': {'confidence_threshold': 0.2}
            }, f)
            temp_path = f.name

        try:
            config = ConfigManager()
            config.load(temp_path)

            # Verify development settings
            assert config.get('logging.level') == 'DEBUG'
            assert config.get('device.type') == 'cpu'
            assert config.get('detection.confidence_threshold') == 0.2

            # Should pass validation
            assert config.validate() is True
        finally:
            os.unlink(temp_path)
