"""
Model versioning system with semantic versioning support.

Provides version parsing, comparison, and compatibility checking for models.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """
    Semantic version for models.

    Follows semantic versioning: MAJOR.MINOR.PATCH
    - MAJOR: Incompatible changes
    - MINOR: Backwards-compatible functionality
    - PATCH: Backwards-compatible bug fixes
    """
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> 'ModelVersion':
        """
        Parse version string into ModelVersion.

        Args:
            version_str: Version string (e.g., "2.1.3", "v2.0.0", "1.0.0-alpha")

        Returns:
            ModelVersion object

        Raises:
            ValueError: If version string is invalid
        """
        if not version_str:
            raise ValueError("Version string cannot be empty")

        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')

        # Match semantic version pattern
        # Format: major.minor.patch[-prerelease]
        pattern = r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-.]([a-zA-Z0-9]+))?$'
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"Invalid version string: {version_str}")

        major = int(match.group(1)) if match.group(1) else 0
        minor = int(match.group(2)) if match.group(2) else 0
        patch = int(match.group(3)) if match.group(3) else 0
        prerelease = match.group(4)

        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease)

    def __str__(self) -> str:
        """String representation of version."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    def __eq__(self, other) -> bool:
        """Check version equality."""
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)

    def __ne__(self, other) -> bool:
        """Check version inequality."""
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        """Check less than."""
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other) -> bool:
        """Check less than or equal."""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """Check greater than."""
        if not isinstance(other, ModelVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other) -> bool:
        """Check greater than or equal."""
        return self > other or self == other


@dataclass
class VersionRange:
    """
    Version range specification for compatibility checking.

    Supports various range formats:
    - Exact: "=2.1.3"
    - Greater than: ">2.0.0"
    - Greater than or equal: ">=2.0.0"
    - Less than: "<3.0.0"
    - Less than or equal: "<=2.5.0"
    - Caret (compatible): "^2.1.3" (>=2.1.3, <3.0.0)
    - Tilde (patch updates): "~2.1.3" (>=2.1.3, <2.2.0)
    - Wildcard: "*" (any version)
    - Hyphen range: "2.0.0 - 2.5.0"
    """
    min_version: Optional[ModelVersion] = None
    max_version: Optional[ModelVersion] = None
    min_inclusive: bool = True
    max_inclusive: bool = True
    exact_version: Optional[ModelVersion] = None
    allow_any: bool = False

    @classmethod
    def parse(cls, range_str: str) -> 'VersionRange':
        """
        Parse version range string.

        Args:
            range_str: Range specification string

        Returns:
            VersionRange object

        Raises:
            ValueError: If range string is invalid
        """
        range_str = range_str.strip()

        # Wildcard - any version
        if range_str == '*' or range_str == '':
            return cls(allow_any=True)

        # Hyphen range: "2.0.0 - 2.5.0"
        if ' - ' in range_str:
            parts = range_str.split(' - ')
            if len(parts) != 2:
                raise ValueError(f"Invalid hyphen range: {range_str}")
            min_ver = ModelVersion.parse(parts[0].strip())
            max_ver = ModelVersion.parse(parts[1].strip())
            return cls(min_version=min_ver, max_version=max_ver,
                      min_inclusive=True, max_inclusive=True)

        # Caret range: ^2.1.3 -> >=2.1.3, <3.0.0
        if range_str.startswith('^'):
            version = ModelVersion.parse(range_str[1:])
            # Max version is next major
            max_ver = ModelVersion(version.major + 1, 0, 0)
            return cls(min_version=version, max_version=max_ver,
                      min_inclusive=True, max_inclusive=False)

        # Tilde range: ~2.1.3 -> >=2.1.3, <2.2.0
        if range_str.startswith('~'):
            version = ModelVersion.parse(range_str[1:])
            # Max version is next minor
            max_ver = ModelVersion(version.major, version.minor + 1, 0)
            return cls(min_version=version, max_version=max_ver,
                      min_inclusive=True, max_inclusive=False)

        # Exact version: =2.1.3
        if range_str.startswith('='):
            version = ModelVersion.parse(range_str[1:])
            return cls(exact_version=version)

        # Greater than or equal: >=2.0.0
        if range_str.startswith('>='):
            version = ModelVersion.parse(range_str[2:])
            return cls(min_version=version, min_inclusive=True)

        # Less than or equal: <=2.5.0
        if range_str.startswith('<='):
            version = ModelVersion.parse(range_str[2:])
            return cls(max_version=version, max_inclusive=True)

        # Greater than: >2.0.0
        if range_str.startswith('>'):
            version = ModelVersion.parse(range_str[1:])
            return cls(min_version=version, min_inclusive=False)

        # Less than: <3.0.0
        if range_str.startswith('<'):
            version = ModelVersion.parse(range_str[1:])
            return cls(max_version=version, max_inclusive=False)

        # If no operator, treat as exact version
        try:
            version = ModelVersion.parse(range_str)
            return cls(exact_version=version)
        except ValueError:
            raise ValueError(f"Invalid version range: {range_str}")

    def is_compatible(self, version: ModelVersion) -> bool:
        """
        Check if version is compatible with this range.

        Args:
            version: Version to check

        Returns:
            True if version is compatible
        """
        if self.allow_any:
            return True

        if self.exact_version:
            return version == self.exact_version

        if self.min_version:
            if self.min_inclusive:
                if version < self.min_version:
                    return False
            else:
                if version <= self.min_version:
                    return False

        if self.max_version:
            if self.max_inclusive:
                if version > self.max_version:
                    return False
            else:
                if version >= self.max_version:
                    return False

        return True


@dataclass
class ModelMetadata:
    """
    Metadata extracted from model files.

    Contains version information and model characteristics.
    """
    version: ModelVersion
    toolkit_version: Optional[ModelVersion] = None
    model_type: Optional[str] = None
    input_shape: Optional[tuple] = None
    output_shape: Optional[tuple] = None
    additional_metadata: dict = None

    def __post_init__(self):
        if self.additional_metadata is None:
            self.additional_metadata = {}


@dataclass
class CompatibilityResult:
    """
    Result of compatibility check.

    Provides detailed compatibility information.
    """
    is_compatible: bool
    warnings: List[str] = None
    suggested_versions: List[str] = None
    reason: str = ""

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggested_versions is None:
            self.suggested_versions = []


class CompatibilityChecker:
    """
    Check model compatibility with toolkit version.

    Uses semantic versioning rules for compatibility determination.
    """

    def __init__(self, toolkit_version: ModelVersion):
        """
        Initialize checker.

        Args:
            toolkit_version: Current toolkit version
        """
        self.toolkit_version = toolkit_version

    def check_compatibility(self, model_version: ModelVersion,
                           toolkit_version_range: Optional[str] = None) -> CompatibilityResult:
        """
        Check if model version is compatible.

        Args:
            model_version: Version of the model to check
            toolkit_version_range: Optional version range string

        Returns:
            CompatibilityResult with detailed information
        """
        warnings = []
        is_compatible = True
        reason = ""

        # Major version mismatch - incompatible
        if model_version.major != self.toolkit_version.major:
            is_compatible = False
            reason = (f"Major version mismatch: model v{model_version} vs "
                     f"toolkit v{self.toolkit_version}")
            suggestions = [
                f"Use model version {self.toolkit_version.major}.x.x",
                f"Update toolkit to version {model_version.major}.x.x"
            ]
            return CompatibilityResult(
                is_compatible=False,
                warnings=[reason],
                suggested_versions=suggestions,
                reason=reason
            )

        # Minor version difference - compatible with warning
        if model_version.minor != self.toolkit_version.minor:
            warnings.append(
                f"Minor version difference: model v{model_version} vs "
                f"toolkit v{self.toolkit_version}. May have compatibility issues."
            )
            reason = "Minor version mismatch - use with caution"

        # Patch version - fully compatible
        if model_version.patch != self.toolkit_version.patch:
            reason = "Patch version difference - fully compatible"

        if not reason:
            reason = "Version match - fully compatible"

        return CompatibilityResult(
            is_compatible=is_compatible,
            warnings=warnings,
            suggested_versions=[str(self.toolkit_version)],
            reason=reason
        )


def extract_metadata(model_path: str) -> ModelMetadata:
    """
    Extract metadata from model file.

    Args:
        model_path: Path to model file (.pt or .onnx)

    Returns:
        ModelMetadata with extracted information

    Raises:
        FileNotFoundError: If model file doesn't exist
        ValueError: If model format is unsupported
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Default version if not found in model
    default_version = ModelVersion(0, 0, 0)
    default_metadata = ModelMetadata(version=default_version)

    # Determine format from extension
    suffix = model_path.suffix.lower()

    if suffix == '.pt':
        return _extract_pt_metadata(model_path)
    elif suffix == '.onnx':
        return _extract_onnx_metadata(model_path)
    else:
        logger.warning(f"Unsupported model format: {suffix}, using default metadata")
        return default_metadata


def _extract_pt_metadata(model_path: Path) -> ModelMetadata:
    """Extract metadata from PyTorch model."""
    try:
        import torch
        # Load with weights_only for security
        checkpoint = torch.load(model_path, weights_only=True, map_location='cpu')

        # Try to extract version from metadata
        version_str = "0.0.0"
        model_type = None

        if isinstance(checkpoint, dict):
            # Try common metadata keys
            metadata = checkpoint.get('_metadata', {})
            if isinstance(metadata, dict):
                version_str = metadata.get('version', version_str)
                model_type = metadata.get('model_type', model_type)
            else:
                # Some models store metadata directly
                version_str = checkpoint.get('version', version_str)
                model_type = checkpoint.get('model_type', model_type)

        # Parse version
        try:
            version = ModelVersion.parse(version_str)
        except ValueError:
            logger.warning(f"Invalid version '{version_str}', using 0.0.0")
            version = ModelVersion(0, 0, 0)

        return ModelMetadata(version=version, model_type=model_type)

    except Exception as e:
        logger.warning(f"Failed to extract PT metadata: {e}, using defaults")
        return ModelMetadata(version=ModelVersion(0, 0, 0))


def _extract_onnx_metadata(model_path: Path) -> ModelMetadata:
    """Extract metadata from ONNX model."""
    try:
        import onnxruntime as ort

        session = ort.InferenceSession(str(model_path))
        meta = session.get_modelmeta()

        # Extract version from custom metadata
        version_str = "0.0.0"
        if meta.custom_metadata_map:
            version_str = meta.custom_metadata_map.get('version', version_str)

        # Parse version
        try:
            version = ModelVersion.parse(version_str)
        except ValueError:
            logger.warning(f"Invalid version '{version_str}', using 0.0.0")
            version = ModelVersion(0, 0, 0)

        # Get input/output shapes
        input_shape = None
        output_shape = None

        if session.get_inputs():
            input_shape = session.get_inputs()[0].shape
        if session.get_outputs():
            output_shape = session.get_outputs()[0].shape

        return ModelMetadata(
            version=version,
            model_type="onnx",
            input_shape=tuple(input_shape) if input_shape else None,
            output_shape=tuple(output_shape) if output_shape else None
        )

    except Exception as e:
        logger.warning(f"Failed to extract ONNX metadata: {e}, using defaults")
        return ModelMetadata(version=ModelVersion(0, 0, 0), model_type="onnx")
