"""
Model version archive and management system.

This module provides archiving and version management for models.
"""

import os
import shutil
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime
import logging

from .versioning import ModelVersion

logger = logging.getLogger(__name__)


@dataclass
class ArchiveEntry:
    """Entry in archive manifest."""
    model_type: str
    version: str
    filename: str
    archived_at: str
    model_path: str
    file_size: int
    metadata: dict


class ModelArchiver:
    """Archive and manage model versions."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize model archiver.

        Args:
            cache_dir: Base cache directory. Defaults to ~/.cache/edge-detection
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/edge-detection")

        self.cache_dir = Path(cache_dir)
        self.archive_dir = self.cache_dir / "models" / "archive"
        self.archive_manifest_path = self.archive_dir / "archive.yaml"

        # Create archive directory if it doesn't exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def archive_model(self, model_path: str, model_type: str, version: ModelVersion) -> str:
        """Archive a model file.

        Args:
            model_path: Path to model file to archive
            model_type: Type of model (e.g., "yolov8n", "yolov10n")
            version: Model version

        Returns:
            Path to archived model
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise IOError(f"Model file not found: {model_path}")

        # Create versioned archive directory
        version_str = str(version).replace('.', '_')  # Replace dots for filesystem safety
        archive_subdir = self.archive_dir / model_type / f"v{version_str}"
        archive_subdir.mkdir(parents=True, exist_ok=True)

        # Destination path
        dest_path = archive_subdir / model_path.name

        # Copy model file
        shutil.copy2(model_path, dest_path)
        logger.info(f"Archived model {model_path} to {dest_path}")

        # Update manifest
        self._add_to_manifest(
            model_type=model_type,
            version=str(version),
            filename=model_path.name,
            archived_path=str(dest_path),
            file_size=dest_path.stat().st_size
        )

        return str(dest_path)

    def list_archived_versions(self, model_type: Optional[str] = None) -> List[ArchiveEntry]:
        """List all archived model versions.

        Args:
            model_type: Filter by model type. If None, list all.

        Returns:
            List of archive entries
        """
        manifest = self._load_manifest()
        entries = []

        for entry_data in manifest.get('archives', []):
            entry = ArchiveEntry(**entry_data)
            if model_type is None or entry.model_type == model_type:
                entries.append(entry)

        return sorted(entries, key=lambda e: e.archived_at, reverse=True)

    def restore_from_archive(self, model_type: str, version: str, dest_path: str) -> str:
        """Restore a model from archive.

        Args:
            model_type: Type of model
            version: Version string (e.g., "2.0.0")
            dest_path: Destination path for restored model

        Returns:
            Path to restored model
        """
        # Find archived version
        entries = self.list_archived_versions(model_type)

        for entry in entries:
            if entry.version == version:
                archive_path = entry.model_path

                if not os.path.exists(archive_path):
                    raise IOError(f"Archived model not found: {archive_path}")

                # Copy from archive
                dest_path = Path(dest_path)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(archive_path, dest_path)

                logger.info(f"Restored model from {archive_path} to {dest_path}")
                return str(dest_path)

        raise ValueError(f"Version {version} not found in archive for {model_type}")

    def _load_manifest(self) -> dict:
        """Load archive manifest file."""
        if not self.archive_manifest_path.exists():
            return {'archives': []}

        try:
            with open(self.archive_manifest_path, 'r') as f:
                return yaml.safe_load(f) or {'archives': []}
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return {'archives': []}

    def _save_manifest(self, manifest: dict):
        """Save archive manifest file."""
        with open(self.archive_manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)

    def _add_to_manifest(self, model_type: str, version: str, filename: str,
                        archived_path: str, file_size: int):
        """Add entry to archive manifest."""
        manifest = self._load_manifest()

        entry = ArchiveEntry(
            model_type=model_type,
            version=version,
            filename=filename,
            archived_at=datetime.now().isoformat(),
            model_path=archived_path,
            file_size=file_size,
            metadata={}
        )

        manifest['archives'].append(asdict(entry))
        self._save_manifest(manifest)


class UpdateLog:
    """Track model update history."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize update log.

        Args:
            cache_dir: Base cache directory. Defaults to ~/.cache/edge-detection
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/edge-detection")

        self.cache_dir = Path(cache_dir)
        self.log_path = self.cache_dir / "models" / "update_log.yaml"

        # Create models directory if it doesn't exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_update(self, model_type: str, old_version: Optional[str],
                  new_version: str, action: str):
        """Log a model update event.

        Args:
            model_type: Type of model
            old_version: Previous version (None if new download)
            new_version: New version
            action: Action performed (download, archive, update)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model_type': model_type,
            'old_version': old_version,
            'new_version': new_version,
            'action': action
        }

        logs = self.get_history()
        logs.append(log_entry)

        # Keep only last 100 entries
        if len(logs) > 100:
            logs = logs[-100:]

        with open(self.log_path, 'w') as f:
            yaml.dump({'updates': logs}, f, default_flow_style=False)

        logger.info(f"Logged update: {model_type} {old_version} -> {new_version} ({action})")

    def get_history(self, model_type: Optional[str] = None,
                   limit: Optional[int] = None) -> List[dict]:
        """Get update history.

        Args:
            model_type: Filter by model type. If None, return all.
            limit: Maximum number of entries to return

        Returns:
            List of update log entries
        """
        if not self.log_path.exists():
            return []

        try:
            with open(self.log_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                logs = data.get('updates', [])
        except Exception as e:
            logger.error(f"Failed to load update log: {e}")
            return []

        # Filter by model type
        if model_type:
            logs = [log for log in logs if log.get('model_type') == model_type]

        # Sort by timestamp descending
        logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)

        # Apply limit
        if limit:
            logs = logs[:limit]

        return logs
