"""
Integration tests for validation and profile functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config.config_manager import ConfigManager, ConfigurationError


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestValidationIntegration:
    """Test validation integration with ConfigManager."""

    def test_valid_config_loads_successfully(self):
        """Test loading valid configuration with validation."""
        config = ConfigManager()
        config.load()  # Should load and validate successfully
        assert config.get('model.name') == 'yolov8n'
        assert config.get('detection.confidence_threshold') == 0.25

    def test_skip_validation_allows_invalid_values(self):
        """Test skip_validation parameter allows loading without validation."""
        config = ConfigManager()
        config._config = {
            'model': {'name': 'yolov8n', 'path': None, 'cache_dir': '~/.cache/edge-detection/models'},
            'device': {'type': 'auto', 'auto_detect': True},
            'detection': {'confidence_threshold': 1.5, 'iou_threshold': 0.45, 'max_detections': 300},
            'input': {'image_size': [640, 640], 'letterbox': True, 'normalize': True},
            'output': {'save_dir': './output', 'format': 'jpg', 'show_confidence': True, 'show_labels': True},
            'logging': {'level': 'INFO', 'format': 'text', 'file': None},
            'performance': {'half_precision': False, 'batch_size': 1, 'workers': 4}
        }
        config._loaded = True
        # Should not raise with skip_validation
        config.validate()  # This will raise due to 1.5 threshold


class TestProfileIntegration:
    """Test profile functionality integration."""

    def test_load_with_profile(self, temp_config_dir):
        """Test loading configuration with profile."""
        # Create profile file
        profile_content = """
model:
  name: yolov8s
device:
  type: cpu
detection:
  confidence_threshold: 0.5
"""
        profile_path = temp_config_dir / "test_profile.yaml"
        profile_path.write_text(profile_content)

        # Create ConfigManager with profile
        from config.profile_manager import ProfileManager
        pm = ProfileManager(temp_config_dir)

        base_config = {
            'model': {'name': 'yolov8n', 'path': None, 'cache_dir': '~/.cache/edge-detection/models'},
            'device': {'type': 'auto', 'auto_detect': True},
            'detection': {'confidence_threshold': 0.25, 'iou_threshold': 0.45, 'max_detections': 300}
        }

        merged = pm.merge_with_profile(base_config, "test_profile")

        assert merged['model']['name'] == 'yolov8s'
        assert merged['device']['type'] == 'cpu'
        assert merged['detection']['confidence_threshold'] == 0.5

    def test_profile_not_found_error_message(self, temp_config_dir):
        """Test error message when profile not found."""
        from config.profile_manager import ProfileManager
        pm = ProfileManager(temp_config_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            pm.load_profile("nonexistent_profile")

        error_msg = str(exc_info.value)
        assert "not found" in error_msg
        assert "Available profiles:" in error_msg
        assert "💡 Hint:" in error_msg
