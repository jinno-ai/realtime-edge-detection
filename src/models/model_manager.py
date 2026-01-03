"""
Model Manager for automatic download and caching of detection models.
"""

from pathlib import Path
from typing import Optional
import hashlib
import logging
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModelDownloadError(Exception):
    """Raised when model download fails."""
    def __init__(self, message: str, model_name: str = None, suggested_action: str = None):
        self.model_name = model_name
        self.suggested_action = suggested_action
        super().__init__(message)


class IntegrityError(Exception):
    """Raised when model integrity validation fails."""
    pass


class ModelManager:
    """
    Manages model download, caching, and validation.

    Implements singleton pattern for consistent model management.
    """

    _instance = None

    # Model download URLs
    BASE_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/"
    MODELS = {
        "yolov8n": "yolov8n.pt",
        "yolov8s": "yolov8s.pt",
        "yolov8m": "yolov8m.pt",
        "yolov8l": "yolov8l.pt",
        "yolov8x": "yolov8x.pt",
    }

    def __new__(cls, cache_dir: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_dir: Optional[Path] = None):
        if hasattr(self, '_initialized'):
            return

        self.cache_dir = cache_dir or self._default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info(f"ModelManager initialized with cache dir: {self.cache_dir}")

    @staticmethod
    def _default_cache_dir() -> Path:
        """Get default cache directory."""
        return Path.home() / ".cache" / "edge-detection" / "models"

    def get_model(self, model_name: str, version: str = "latest", force_download: bool = False) -> Path:
        """
        Get model path, downloading if necessary.

        Args:
            model_name: Name of the model (e.g., "yolov8n")
            version: Model version (not currently used, for future)
            force_download: Force re-download even if cached

        Returns:
            Path to the model file
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.MODELS.keys())}")

        model_filename = self.MODELS[model_name]
        model_path = self.cache_dir / model_filename

        # Check if model is cached and valid
        if model_path.exists() and not force_download:
            if self._validate_integrity(model_path):
                logger.info(f"Using cached model: {model_path}")
                return model_path
            else:
                logger.warning(f"Cached model corrupted, re-downloading: {model_path}")

        # Download the model
        return self.download_model(model_name, version)

    def download_model(self, model_name: str, version: str = "latest") -> Path:
        """
        Download model with progress display and retry logic.

        Args:
            model_name: Name of the model to download
            version: Model version

        Returns:
            Path to the downloaded model
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        model_filename = self.MODELS[model_name]
        model_url = self.BASE_URL + model_filename
        model_path = self.cache_dir / model_filename

        logger.info(f"Downloading {model_name} from {model_url}")

        success = self._download_with_retry(model_url, model_path, max_retries=3)

        if not success:
            raise ModelDownloadError(
                f"Failed to download model {model_name} after 3 attempts",
                model_name=model_name,
                suggested_action=f"Check internet connection or download manually from {model_url}"
            )

        logger.info(f"Model downloaded successfully: {model_path}")
        return model_path

    def _download_with_retry(self, url: str, dest_path: Path, max_retries: int = 3) -> bool:
        """
        Download with exponential backoff retry.

        Args:
            url: URL to download from
            dest_path: Destination path for the file
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))

                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading model") as progress_bar:
                    with open(dest_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress_bar.update(len(chunk))

                return True

            except (requests.RequestException, IOError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Download failed (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"Download failed after {max_retries} attempts: {e}")

        return False

    def _validate_integrity(self, model_path: Path, expected_checksum: Optional[str] = None) -> bool:
        """
        Validate model file using SHA256 checksum.

        Args:
            model_path: Path to the model file
            expected_checksum: Expected SHA256 checksum (optional)

        Returns:
            True if valid, False otherwise
        """
        if not model_path.exists():
            return False

        try:
            sha256_hash = hashlib.sha256()
            with open(model_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            calculated_checksum = sha256_hash.hexdigest()

            # If expected checksum provided, verify it
            if expected_checksum:
                return calculated_checksum == expected_checksum

            # For now, assume file is valid if it exists and is readable
            # TODO: Implement official checksum verification
            return True

        except (IOError, OSError) as e:
            logger.error(f"Integrity check failed for {model_path}: {e}")
            return False

    def load_custom_model(self, model_path: Path) -> Path:
        """
        Load custom model from specified path.

        Args:
            model_path: Path to custom model file

        Returns:
            Path to the model

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model file is invalid
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Custom model not found: {model_path}")

        if not model_path.is_file():
            raise ValueError(f"Model path is not a file: {model_path}")

        # Basic validation - check if file is readable
        try:
            with open(model_path, 'rb') as f:
                f.read(1)
        except IOError as e:
            raise ValueError(f"Cannot read model file: {e}")

        logger.info(f"Using custom model: {model_path}")
        return model_path

    def clear_cache(self, older_than_days: Optional[int] = None) -> None:
        """
        Clear cached models.

        Args:
            older_than_days: Only delete models older than this many days (optional)
        """
        import time

        current_time = time.time()

        for model_file in self.cache_dir.glob("*.pt"):
            if older_than_days is not None:
                file_age = current_time - model_file.stat().st_mtime
                if file_age < older_than_days * 86400:
                    continue

            logger.info(f"Deleting cached model: {model_file}")
            model_file.unlink()
