"""
Unit tests for ModelManager.

Tests model download, caching, and validation functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import hashlib
import requests

from src.models.model_manager import ModelManager, ModelDownloadError, IntegrityError


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache" / "models"
    cache_dir.mkdir(parents=True)
    return cache_dir


@pytest.fixture
def model_manager(temp_cache_dir):
    """Create a ModelManager instance with temporary cache."""
    # Reset singleton for testing
    ModelManager._instance = None
    return ModelManager(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_model_file(temp_cache_dir):
    """Create a mock model file for testing."""
    model_path = temp_cache_dir / "yolov8n.pt"
    model_path.write_bytes(b"fake model data for testing")
    return model_path


class TestModelManagerInit:
    """Test ModelManager initialization."""

    def test_singleton_pattern(self, temp_cache_dir):
        """Test that ModelManager implements singleton pattern."""
        ModelManager._instance = None

        manager1 = ModelManager(cache_dir=temp_cache_dir)
        manager2 = ModelManager(cache_dir=temp_cache_dir)

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_cache_dir_creation(self, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        ModelManager._instance = None
        cache_dir = tmp_path / "new_cache"

        ModelManager(cache_dir=cache_dir)

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_default_cache_dir(self):
        """Test default cache directory location."""
        ModelManager._instance = None
        manager = ModelManager()

        expected_dir = Path.home() / ".cache" / "edge-detection" / "models"
        assert manager.cache_dir == expected_dir


class TestModelDownload:
    """Test model download functionality."""

    def test_download_with_success(self, model_manager, mock_model_file):
        """Test successful model download."""
        with patch.object(model_manager, '_download_with_retry', return_value=True):
            model_path = model_manager.download_model("yolov8n")
            assert model_path.name == "yolov8n.pt"

    def test_download_with_failure(self, model_manager):
        """Test download failure after retries."""
        with patch.object(model_manager, '_download_with_retry', return_value=False):
            with pytest.raises(ModelDownloadError) as exc_info:
                model_manager.download_model("yolov8n")

            assert "Failed to download model" in str(exc_info.value)
            assert exc_info.value.model_name == "yolov8n"

    def test_download_unknown_model(self, model_manager):
        """Test downloading an unknown model raises error."""
        with pytest.raises(ValueError) as exc_info:
            model_manager.download_model("unknown_model")

        assert "Unknown model" in str(exc_info.value)


class TestRetryLogic:
    """Test download retry logic."""

    @patch('requests.get')
    def test_retry_on_failure(self, mock_get, model_manager):
        """Test that download retries on failure."""
        # Fail first two attempts, succeed on third
        mock_response = Mock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content.return_value = [b"data"]
        mock_response.raise_for_status = Mock()

        # First two attempts fail
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response  # Third attempt succeeds
        ]

        url = "http://test.com/model.pt"
        dest_path = model_manager.cache_dir / "model.pt"

        result = model_manager._download_with_retry(url, dest_path, max_retries=3)

        assert result is True
        assert mock_get.call_count == 3

    @patch('requests.get')
    def test_exponential_backoff(self, mock_get, model_manager):
        """Test exponential backoff between retries."""
        mock_get.side_effect = requests.RequestException("Network error")

        with patch('time.sleep') as mock_sleep:
            result = model_manager._download_with_retry(
                "http://test.com/model.pt",
                model_manager.cache_dir / "model.pt",
                max_retries=3
            )

            assert result is False
            # Should sleep with exponential backoff: 1s, 2s
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)


class TestModelCaching:
    """Test model caching functionality."""

    def test_get_model_uses_cache(self, model_manager, mock_model_file):
        """Test that cached model is used if available and valid."""
        with patch.object(model_manager, '_validate_integrity', return_value=True):
            with patch.object(model_manager, 'download_model') as mock_download:
                model_path = model_manager.get_model("yolov8n")

                assert model_path == mock_model_file
                mock_download.assert_not_called()

    def test_get_model_downloads_if_not_cached(self, model_manager):
        """Test that model is downloaded if not in cache."""
        with patch.object(model_manager, 'download_model') as mock_download:
            mock_download.return_value = model_manager.cache_dir / "yolov8n.pt"

            model_manager.get_model("yolov8n")

            mock_download.assert_called_once_with("yolov8n", "latest")

    def test_get_model_retries_if_corrupted(self, model_manager, mock_model_file):
        """Test that corrupted cached model triggers re-download."""
        with patch.object(model_manager, '_validate_integrity', return_value=False):
            with patch.object(model_manager, 'download_model') as mock_download:
                mock_download.return_value = mock_model_file

                model_manager.get_model("yolov8n")

                mock_download.assert_called_once()


class TestIntegrityValidation:
    """Test model integrity validation."""

    def test_validate_valid_file(self, model_manager, mock_model_file):
        """Test validation of valid model file."""
        result = model_manager._validate_integrity(mock_model_file)
        assert result is True

    def test_validate_missing_file(self, model_manager):
        """Test validation fails for missing file."""
        result = model_manager._validate_integrity(Path("nonexistent.pt"))
        assert result is False

    def test_validate_with_checksum(self, model_manager, mock_model_file):
        """Test validation with expected checksum."""
        # Calculate actual checksum
        sha256_hash = hashlib.sha256()
        with open(mock_model_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        expected_checksum = sha256_hash.hexdigest()

        result = model_manager._validate_integrity(mock_model_file, expected_checksum)
        assert result is True

    def test_validate_with_wrong_checksum(self, model_manager, mock_model_file):
        """Test validation fails with wrong checksum."""
        wrong_checksum = "0" * 64
        result = model_manager._validate_integrity(mock_model_file, wrong_checksum)
        assert result is False


class TestCustomModelLoading:
    """Test custom model loading functionality."""

    def test_load_custom_model_success(self, model_manager, mock_model_file):
        """Test successful custom model loading."""
        result = model_manager.load_custom_model(mock_model_file)
        assert result == mock_model_file

    def test_load_custom_model_not_found(self, model_manager):
        """Test loading non-existent custom model raises error."""
        with pytest.raises(FileNotFoundError) as exc_info:
            model_manager.load_custom_model(Path("nonexistent.pt"))

        assert "not found" in str(exc_info.value).lower()

    def test_load_custom_model_directory(self, model_manager, temp_cache_dir):
        """Test that loading a directory raises error."""
        with pytest.raises(ValueError) as exc_info:
            model_manager.load_custom_model(temp_cache_dir)

        assert "not a file" in str(exc_info.value)

    def test_load_custom_model_unreadable(self, model_manager, tmp_path):
        """Test loading unreadable file raises error."""
        unreadable_file = tmp_path / "unreadable.pt"
        unreadable_file.write_bytes(b"data")

        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError) as exc_info:
                model_manager.load_custom_model(unreadable_file)

            assert "Cannot read" in str(exc_info.value)


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache_all(self, model_manager, mock_model_file):
        """Test clearing all cached models."""
        model_manager.clear_cache()

        assert not mock_model_file.exists()

    def test_clear_cache_older_than(self, model_manager, mock_model_file):
        """Test clearing models older than specified days."""
        import time

        # Create an old model file
        old_model = model_manager.cache_dir / "old.pt"
        old_model.write_bytes(b"old data")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 86400)
        import os
        os.utime(old_model, (old_time, old_time))

        # Clear models older than 5 days
        model_manager.clear_cache(older_than_days=5)

        # Old model should be deleted, recent model should remain
        assert not old_model.exists()
        assert mock_model_file.exists()


class TestModelRegistry:
    """Test model name and URL registry."""

    def test_available_models(self, model_manager):
        """Test available model names."""
        expected_models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
        for model in expected_models:
            assert model in model_manager.MODELS

    def test_model_urls(self, model_manager):
        """Test that model URLs are properly formatted."""
        for model_name, filename in model_manager.MODELS.items():
            expected_url = model_manager.BASE_URL + filename
            assert expected_url.startswith("https://github.com")
