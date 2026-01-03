"""
Model versioning and compatibility checking system.

This module provides semantic versioning support for models with compatibility checking.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class CompatibilityStatus(Enum):
    """Compatibility check result status."""
    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_WARNING = "compatible_with_warning"
    INCOMPATIBLE = "incompatible"


@dataclass
class ModelVersion:
    """Semantic version for models."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> 'ModelVersion':
        """Parse version string into ModelVersion.

        Args:
            version_str: Version string (e.g., "2.0.0", "v2.1.0", "2.0.0-beta")

        Returns:
            ModelVersion instance
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')

        # Parse version and prerelease
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$', version_str)
        if not match:
            # Try simpler version format
            match = re.match(r'^(\d+)\.(\d+)$', version_str)
            if match:
                return cls(int(match.group(1)), int(match.group(2)), 0)
            # Default to 0.0.0 for unparseable versions
            logger.warning(f"Cannot parse version '{version_str}', defaulting to 0.0.0")
            return cls(0, 0, 0)

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4)

        return cls(major, minor, patch, prerelease)

    def __str__(self) -> str:
        """String representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    def __eq__(self, other) -> bool:
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other) -> bool:
        return not self.__le__(other)

    def __ge__(self, other) -> bool:
        return not self.__lt__(other)


@dataclass
class VersionRange:
    """Version range for compatibility checking."""
    min_version: Optional[ModelVersion] = None
    max_version: Optional[ModelVersion] = None

    def is_compatible(self, version: ModelVersion) -> bool:
        """Check if version falls within range.

        Args:
            version: Version to check

        Returns:
            True if version is within range
        """
        if self.min_version and version < self.min_version:
            return False
        if self.max_version and version > self.max_version:
            return False
        return True


@dataclass
class ModelMetadata:
    """Metadata extracted from model files."""
    version: ModelVersion
    toolkit_version: ModelVersion
    model_type: str
    input_shape: Tuple[int, ...]
    output_shape: Tuple[int, ...]
    additional_info: dict = None

    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class CompatibilityResult:
    """Result of compatibility check."""
    is_compatible: bool
    status: CompatibilityStatus
    warnings: List[str]
    suggested_versions: List[str]
    message: str


class CompatibilityChecker:
    """Check model-toolkit version compatibility."""

    def __init__(self, toolkit_version: str):
        """Initialize compatibility checker.

        Args:
            toolkit_version: Current toolkit version (e.g., "2.0.0")
        """
        self.toolkit_version = ModelVersion.parse(toolkit_version)

    def check_compatibility(self, model_version: ModelVersion) -> CompatibilityResult:
        """Check compatibility between model and toolkit versions.

        Compatibility rules:
        - Major version mismatch: Incompatible (e.g., 1.x vs 2.x)
        - Minor version difference: Compatible with warning (e.g., 2.0 vs 2.1)
        - Patch version: Fully compatible (e.g., 2.0.0 vs 2.0.1)

        Args:
            model_version: Model version to check

        Returns:
            CompatibilityResult with check outcome
        """
        warnings = []
        suggested_versions = []

        # Major version mismatch
        if model_version.major != self.toolkit_version.major:
            suggested_versions.append(f"v{self.toolkit_version.major}.x.x")
            return CompatibilityResult(
                is_compatible=False,
                status=CompatibilityStatus.INCOMPATIBLE,
                warnings=[],
                suggested_versions=suggested_versions,
                message=(
                    f"Model version {model_version} is not compatible with "
                    f"current toolkit version {self.toolkit_version}. "
                    f"Compatible models: {self.toolkit_version.major}.x.x"
                )
            )

        # Minor version difference
        if model_version.minor != self.toolkit_version.minor:
            warnings.append(
                f"Model version {model_version} minor version differs from "
                f"toolkit version {self.toolkit_version}. "
                f"This may work but is not tested."
            )
            return CompatibilityResult(
                is_compatible=True,
                status=CompatibilityStatus.COMPATIBLE_WITH_WARNING,
                warnings=warnings,
                suggested_versions=[f"v{self.toolkit_version.major}.{self.toolkit_version.minor}.x"],
                message=f"Loaded model: version {model_version} (compatible with warnings)"
            )

        # Patch version or exact match
        return CompatibilityResult(
            is_compatible=True,
            status=CompatibilityStatus.COMPATIBLE,
            warnings=warnings,
            suggested_versions=[],
            message=f"Loaded model: version {model_version} (compatible)"
        )


def extract_metadata(model_path: str) -> ModelMetadata:
    """Extract metadata from model file.

    Args:
        model_path: Path to model file (.pt or .onnx)

    Returns:
        ModelMetadata with extracted information

    Raises:
        ValueError: If model file format is not supported
        IOError: If model file cannot be read
    """
    import torch
    import os

    if not os.path.exists(model_path):
        raise IOError(f"Model file not found: {model_path}")

    file_ext = os.path.splitext(model_path)[1].lower()

    if file_ext == '.pt':
        return _extract_pytorch_metadata(model_path)
    elif file_ext == '.onnx':
        return _extract_onnx_metadata(model_path)
    else:
        raise ValueError(f"Unsupported model format: {file_ext}. Supported: .pt, .onnx")


def _extract_pytorch_metadata(model_path: str) -> ModelMetadata:
    """Extract metadata from PyTorch model file."""
    import torch

    try:
        # Load model with weights_only for security
        state_dict = torch.load(model_path, weights_only=True, map_location='cpu')
    except Exception as e:
        logger.error(f"Failed to load PyTorch model: {e}")
        raise IOError(f"Failed to load model file: {e}")

    # Extract version from metadata
    metadata = state_dict.get('_metadata', {})
    model_version = ModelVersion.parse(metadata.get('version', '0.0.0'))
    toolkit_version = ModelVersion.parse(metadata.get('toolkit_version', '1.0.0'))
    model_type = metadata.get('model_type', 'unknown')

    # Try to get input/output shapes from model
    input_shape = metadata.get('input_shape', (640, 640, 3))
    output_shape = metadata.get('output_shape', (8400, 85))

    # If not in metadata, try to infer from state_dict
    if 'input_shape' not in metadata and 'model' in state_dict:
        # This would be a full model, try to get shapes
        # For now, use defaults
        pass

    additional_info = {k: v for k, v in metadata.items()
                      if k not in ['version', 'toolkit_version', 'model_type', 'input_shape', 'output_shape']}

    return ModelMetadata(
        version=model_version,
        toolkit_version=toolkit_version,
        model_type=model_type,
        input_shape=tuple(input_shape) if isinstance(input_shape, list) else input_shape,
        output_shape=tuple(output_shape) if isinstance(output_shape, list) else output_shape,
        additional_info=additional_info
    )


def _extract_onnx_metadata(model_path: str) -> ModelMetadata:
    """Extract metadata from ONNX model file."""
    import onnxruntime as ort

    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    except Exception as e:
        logger.error(f"Failed to load ONNX model: {e}")
        raise IOError(f"Failed to load ONNX model: {e}")

    # Get model metadata
    model_meta = session.get_modelmeta()

    # Extract version from custom metadata
    custom_metadata = model_meta.custom_metadata_map if model_meta else {}
    model_version = ModelVersion.parse(custom_metadata.get('version', '0.0.0'))
    toolkit_version = ModelVersion.parse(custom_metadata.get('toolkit_version', '1.0.0'))
    model_type = custom_metadata.get('model_type', 'unknown')

    # Get input/output shapes from model
    input_shape = (640, 640, 3)  # Default
    output_shape = (8400, 85)    # Default

    if session.get_inputs():
        input_info = session.get_inputs()[0]
        input_shape = tuple(input_info.shape if all(isinstance(d, int) for d in input_info.shape) else [640, 640, 3])

    if session.get_outputs():
        output_info = session.get_outputs()[0]
        output_shape = tuple(output_info.shape if all(isinstance(d, int) for d in output_info.shape) else [8400, 85])

    additional_info = {k: v for k, v in custom_metadata.items()
                      if k not in ['version', 'toolkit_version', 'model_type']}

    return ModelMetadata(
        version=model_version,
        toolkit_version=toolkit_version,
        model_type=model_type,
        input_shape=input_shape,
        output_shape=output_shape,
        additional_info=additional_info
    )
