"""
Unit tests for model archiving system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.models.archiver import ModelArchiver, ArchiveEntry
from src.models.versioning import ModelVersion


class TestModelArchiver:
    """Test ModelArchiver class functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def archiver(self, temp_cache_dir):
        """Create archiver instance with temp directory."""
        return ModelArchiver(cache_dir=temp_cache_dir)

    @pytest.fixture
    def temp_model_file(self):
        """Create temporary model file."""
        temp_dir = tempfile.mkdtemp()
        model_path = Path(temp_dir) / "yolov8n.pt"
        model_path.write_text("fake model data")
        yield model_path
        shutil.rmtree(temp_dir)

    def test_archive_model(self, archiver, temp_model_file):
        """Test archiving a model."""
        version = ModelVersion(2, 0, 0)
        archive_path = archiver.archive_model(
            str(temp_model_file),
            version,
            "yolov8n",
            {"format": "pt"}
        )

        assert Path(archive_path).exists()
        assert archiver.archive_dir.exists()
        assert len(archiver.manifest['archives']) == 1

    def test_list_archived_versions(self, archiver, temp_model_file):
        """Test listing archived versions."""
        version1 = ModelVersion(2, 0, 0)
        version2 = ModelVersion(2, 1, 0)

        archiver.archive_model(str(temp_model_file), version1, "yolov8n")
        archiver.archive_model(str(temp_model_file), version2, "yolov8n")

        versions = archiver.list_archived_versions("yolov8n")
        assert len(versions) == 2

    def test_restore_from_archive(self, archiver, temp_model_file):
        """Test restoring from archive."""
        version = ModelVersion(2, 0, 0)

        # Archive model
        archiver.archive_model(str(temp_model_file), version, "yolov8n")

        # Restore to new location
        restore_dir = tempfile.mkdtemp()
        restore_path = Path(restore_dir) / "restored.pt"

        result = archiver.restore_from_archive(
            "yolov8n",
            version,
            str(restore_path)
        )

        assert Path(result).exists()
        shutil.rmtree(restore_dir)
