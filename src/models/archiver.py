"""
Model archiving system for version management.

Handles archiving old model versions and managing model history.
"""

import os
import shutil
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime

from .versioning import ModelVersion

logger = logging.getLogger(__name__)


@dataclass
class ArchiveEntry:
    """Single archive entry."""
    model_name: str
    version: str
    archived_at: str
    original_path: str
    archive_path: str
    metadata: dict


class ModelArchiver:
    """
    Manage model version archiving and restoration.

    Archives old model versions when new ones are downloaded.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize archiver.

        Args:
            cache_dir: Base cache directory (defaults to ~/.cache/edge-detection)
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/edge-detection")

        self.cache_dir = Path(cache_dir)
        self.archive_dir = self.cache_dir / "models" / "archive"
        self.manifest_path = self.archive_dir / "archive.yaml"

        # Create archive directory
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Load or create manifest
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict:
        """Load archive manifest."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    return yaml.safe_load(f) or {'archives': []}
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")
                return {'archives': []}
        return {'archives': []}

    def _save_manifest(self):
        """Save archive manifest."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w') as f:
            yaml.dump(self.manifest, f, default_flow_style=False)

    def archive_model(self, model_path: str, version: ModelVersion,
                      model_name: str, metadata: Optional[dict] = None) -> str:
        """
        Archive a model version.

        Args:
            model_path: Path to model file to archive
            version: Version of the model
            model_name: Name of the model (e.g., "yolov8n")
            metadata: Additional metadata to store

        Returns:
            Path to archived model
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Create model-specific archive directory
        model_archive_dir = self.archive_dir / model_name / f"v{version}"
        model_archive_dir.mkdir(parents=True, exist_ok=True)

        # Archive path
        archive_path = model_archive_dir / model_path.name

        # Copy model to archive
        shutil.copy2(model_path, archive_path)

        # Create archive entry
        entry = ArchiveEntry(
            model_name=model_name,
            version=str(version),
            archived_at=datetime.now().isoformat(),
            original_path=str(model_path),
            archive_path=str(archive_path),
            metadata=metadata or {}
        )

        # Update manifest
        self.manifest['archives'].append(asdict(entry))
        self._save_manifest()

        logger.info(f"Archived {model_name} v{version} to {archive_path}")
        return str(archive_path)

    def list_archived_versions(self, model_name: str) -> List[ArchiveEntry]:
        """
        List all archived versions of a model.

        Args:
            model_name: Name of the model

        Returns:
            List of archive entries
        """
        entries = []
        for entry_dict in self.manifest.get('archives', []):
            if entry_dict.get('model_name') == model_name:
                entries.append(ArchiveEntry(**entry_dict))
        return sorted(entries, key=lambda x: x.archived_at, reverse=True)

    def restore_from_archive(self, model_name: str, version: ModelVersion,
                             restore_path: str) -> str:
        """
        Restore a model from archive.

        Args:
            model_name: Name of the model
            version: Version to restore
            restore_path: Where to restore the model

        Returns:
            Path to restored model
        """
        # Find archive entry
        version_str = str(version)
        archive_entry = None

        for entry_dict in self.manifest.get('archives', []):
            if (entry_dict.get('model_name') == model_name and
                entry_dict.get('version') == version_str):
                archive_entry = ArchiveEntry(**entry_dict)
                break

        if not archive_entry:
            raise FileNotFoundError(
                f"No archived version found for {model_name} v{version}"
            )

        # Copy from archive
        archive_path = Path(archive_entry.archive_path)
        restore_path = Path(restore_path)
        restore_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(archive_path, restore_path)

        logger.info(f"Restored {model_name} v{version} to {restore_path}")
        return str(restore_path)

    def get_archive_path(self, model_name: str, version: ModelVersion) -> Optional[str]:
        """
        Get archive path for a specific model version.

        Args:
            model_name: Name of the model
            version: Version to look up

        Returns:
            Archive path if found, None otherwise
        """
        version_str = str(version)
        for entry_dict in self.manifest.get('archives', []):
            if (entry_dict.get('model_name') == model_name and
                entry_dict.get('version') == version_str):
                return entry_dict.get('archive_path')
        return None
