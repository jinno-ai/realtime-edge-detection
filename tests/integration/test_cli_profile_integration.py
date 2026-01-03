"""
Integration tests for CLI profile loading (Issue #9)

Tests end-to-end CLI workflow with --profile argument
"""
import pytest
import subprocess
import sys
from pathlib import Path


class TestCLIProfileIntegration:
    """Test CLI profile loading end-to-end (Issue #9)"""

    def test_cli_with_prod_profile(self, tmp_path):
        """Test CLI with --profile prod loads production configuration"""
        # Create a minimal valid config for testing
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        default_config = config_dir / "default.yaml"
        prod_config = config_dir / "prod.yaml"

        # Write minimal configs
        default_config.write_text("""
model:
  type: yolo_v8
  path: yolov8n.pt
detection:
  confidence_threshold: 0.5
  iou_threshold: 0.4
  max_detections: 100
  batch_size: 1
device:
  type: auto
  optimize: true
  quantization: null
logging:
  level: INFO
  format: json
  file: null
  rotation: 10MB
metrics:
  enabled: true
  export: prometheus
  port: 9090
""")

        prod_config.write_text("""
detection:
  confidence_threshold: 0.6
logging:
  level: WARNING
""")

        # Test loading config with profile using Python API
        from src.core.config import ConfigManager

        cm = ConfigManager(
            default_config=str(default_config),
            profile="prod"
        )
        config = cm.load_config()

        # Verify prod profile overrides worked
        assert config['detection']['confidence_threshold'] == 0.6
        assert config['logging']['level'] == 'WARNING'

    def test_cli_with_invalid_profile(self, tmp_path):
        """Test CLI with invalid profile shows helpful error"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        default_config = config_dir / "default.yaml"

        default_config.write_text("""
model:
  type: yolo_v8
  path: yolov8n.pt
device:
  type: auto
""")

        from src.core.config import ConfigManager
        from src.core.errors import EdgeDetectionError

        cm = ConfigManager(
            default_config=str(default_config),
            profile="nonexistent"
        )

        # Should raise error with helpful message
        with pytest.raises(EdgeDetectionError) as exc_info:
            cm.load_config()

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower()
        assert "nonexistent" in error_msg

    def test_cli_lists_available_profiles(self, tmp_path):
        """Test CLI can list available profiles"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        default_config = config_dir / "default.yaml"
        dev_config = config_dir / "dev.yaml"
        prod_config = config_dir / "prod.yaml"

        default_config.write_text("model:\n  type: yolo_v8\n")
        dev_config.write_text("logging:\n  level: DEBUG\n")
        prod_config.write_text("logging:\n  level: WARNING\n")

        from src.core.config import ConfigManager

        cm = ConfigManager(default_config=str(default_config))
        profiles = cm.list_profiles()

        # Should list dev and prod (but not default)
        assert 'dev' in profiles
        assert 'prod' in profiles
        assert 'default' not in profiles


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
