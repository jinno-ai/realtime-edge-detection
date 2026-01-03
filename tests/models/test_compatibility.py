"""
Unit tests for compatibility checking system.
"""

import pytest
from src.models.versioning import (
    ModelVersion, CompatibilityChecker, CompatibilityResult,
    extract_metadata
)


class TestCompatibilityChecker:
    """Test CompatibilityChecker class functionality."""

    def test_compatible_same_version(self):
        """Test compatibility with same version."""
        toolkit_version = ModelVersion(2, 0, 0)
        model_version = ModelVersion(2, 0, 0)

        checker = CompatibilityChecker(toolkit_version)
        result = checker.check_compatibility(model_version)

        assert result.is_compatible
        assert len(result.warnings) == 0

    def test_incompatible_major_version(self):
        """Test incompatibility with different major version."""
        toolkit_version = ModelVersion(2, 0, 0)
        model_version = ModelVersion(1, 0, 0)

        checker = CompatibilityChecker(toolkit_version)
        result = checker.check_compatibility(model_version)

        assert not result.is_compatible
        assert len(result.warnings) > 0
        assert "Major version mismatch" in result.reason

    def test_compatible_with_minor_warning(self):
        """Test compatibility with minor version difference."""
        toolkit_version = ModelVersion(2, 0, 0)
        model_version = ModelVersion(2, 1, 0)

        checker = CompatibilityChecker(toolkit_version)
        result = checker.check_compatibility(model_version)

        assert result.is_compatible
        assert len(result.warnings) == 1
        assert "Minor version difference" in result.warnings[0]

    def test_compatible_patch_version(self):
        """Test compatibility with patch version difference."""
        toolkit_version = ModelVersion(2, 0, 0)
        model_version = ModelVersion(2, 0, 1)

        checker = CompatibilityChecker(toolkit_version)
        result = checker.check_compatibility(model_version)

        assert result.is_compatible
        assert len(result.warnings) == 0
