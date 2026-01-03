"""
Unit tests for profile management.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config.profile_manager import ProfileManager


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def profile_manager(temp_config_dir):
    """Create ProfileManager instance with temporary directory."""
    return ProfileManager(temp_config_dir)


class TestProfileManager:
    """Test ProfileManager functionality."""

    def test_list_available_profiles_empty(self, profile_manager):
        """Test listing profiles when directory is empty."""
        profiles = profile_manager.list_available_profiles()
        assert profiles == []

    def test_list_available_profiles(self, temp_config_dir, profile_manager):
        """Test listing available profiles."""
        # Create some profile files
        (temp_config_dir / "dev.yaml").touch()
        (temp_config_dir / "prod.yaml").touch()
        (temp_config_dir / "testing.yaml").touch()
        (temp_config_dir / "default.yaml").touch()  # Should be excluded
        (temp_config_dir / "example.yaml").touch()  # Should be excluded

        profiles = profile_manager.list_available_profiles()
        assert sorted(profiles) == ["dev", "prod", "testing"]

    def test_load_profile_success(self, temp_config_dir, profile_manager):
        """Test loading existing profile."""
        profile_content = """
model:
  name: yolov8s
device:
  type: cpu
"""
        profile_path = temp_config_dir / "dev.yaml"
        profile_path.write_text(profile_content)

        config = profile_manager.load_profile("dev")
        assert config["model"]["name"] == "yolov8s"
        assert config["device"]["type"] == "cpu"

    def test_load_profile_not_found(self, profile_manager):
        """Test loading non-existent profile raises error."""
        with pytest.raises(FileNotFoundError) as exc_info:
            profile_manager.load_profile("nonexistent")

        error_msg = str(exc_info.value)
        assert "not found" in error_msg
        assert "Available profiles:" in error_msg

    def test_load_profile_invalid_yaml(self, temp_config_dir, profile_manager):
        """Test loading profile with invalid YAML raises error."""
        invalid_yaml = """
model:
  name: yolov8n
  path: [unclosed list
"""
        profile_path = temp_config_dir / "invalid.yaml"
        profile_path.write_text(invalid_yaml)

        with pytest.raises(ValueError) as exc_info:
            profile_manager.load_profile("invalid")

        error_msg = str(exc_info.value)
        assert "Invalid YAML" in error_msg
        assert "💡 Hint:" in error_msg

    def test_deep_merge_simple(self, profile_manager):
        """Test deep merge with simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = profile_manager.deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self, profile_manager):
        """Test deep merge with nested dictionaries."""
        base = {
            "model": {"name": "yolov8n", "path": "old.pt"},
            "device": {"type": "auto"}
        }
        override = {
            "model": {"name": "yolov8s"},
            "device": {"type": "cpu"}
        }
        result = profile_manager.deep_merge(base, override)

        assert result["model"]["name"] == "yolov8s"
        assert result["model"]["path"] == "old.pt"  # Preserved
        assert result["device"]["type"] == "cpu"

    def test_merge_with_profile(self, temp_config_dir, profile_manager):
        """Test merging base config with profile."""
        base_config = {
            "model": {"name": "yolov8n", "path": "default.pt"},
            "detection": {"confidence_threshold": 0.25}
        }

        profile_content = """
model:
  name: yolov8s
detection:
  confidence_threshold: 0.5
"""
        profile_path = temp_config_dir / "prod.yaml"
        profile_path.write_text(profile_content)

        merged = profile_manager.merge_with_profile(base_config, "prod")

        assert merged["model"]["name"] == "yolov8s"
        assert merged["model"]["path"] == "default.pt"  # Preserved from base
        assert merged["detection"]["confidence_threshold"] == 0.5
