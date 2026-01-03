"""
Unit tests for model versioning system.

Tests version parsing, comparison, and semantic versioning logic.
"""

import pytest
from src.models.versioning import ModelVersion, VersionRange


class TestModelVersion:
    """Test ModelVersion class functionality."""

    def test_parse_full_version(self):
        """Test parsing full semantic version with all components."""
        version = ModelVersion.parse("2.1.3")
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 3
        assert version.prerelease is None

    def test_parse_version_with_prerelease(self):
        """Test parsing version with prerelease tag."""
        version = ModelVersion.parse("1.0.0-alpha")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.prerelease == "alpha"

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        version = ModelVersion.parse("v2.0.0")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0

    def test_parse_partial_version(self):
        """Test parsing partial version (major.minor only)."""
        version = ModelVersion.parse("2.1")
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 0

    def test_parse_major_only(self):
        """Test parsing major version only."""
        version = ModelVersion.parse("2")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0

    def test_version_equality(self):
        """Test version equality comparison."""
        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(2, 1, 3)
        assert v1 == v2

    def test_version_inequality(self):
        """Test version inequality comparison."""
        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(2, 1, 4)
        assert v1 != v2

    def test_version_less_than(self):
        """Test less than comparison."""
        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(2, 2, 0)
        assert v1 < v2

        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(3, 0, 0)
        assert v1 < v2

    def test_version_greater_than(self):
        """Test greater than comparison."""
        v1 = ModelVersion(2, 2, 0)
        v2 = ModelVersion(2, 1, 3)
        assert v1 > v2

    def test_version_less_than_or_equal(self):
        """Test less than or equal comparison."""
        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(2, 1, 3)
        assert v1 <= v2

        v1 = ModelVersion(2, 1, 2)
        v2 = ModelVersion(2, 1, 3)
        assert v1 <= v2

    def test_version_greater_than_or_equal(self):
        """Test greater than or equal comparison."""
        v1 = ModelVersion(2, 1, 3)
        v2 = ModelVersion(2, 1, 3)
        assert v1 >= v2

        v1 = ModelVersion(2, 1, 4)
        v2 = ModelVersion(2, 1, 3)
        assert v1 >= v2

    def test_version_string_representation(self):
        """Test string representation of version."""
        version = ModelVersion(2, 1, 3)
        assert str(version) == "2.1.3"

        version = ModelVersion(1, 0, 0, "alpha")
        assert str(version) == "1.0.0-alpha"

    def test_version_from_dataclass(self):
        """Test creating version directly via dataclass."""
        version = ModelVersion(major=2, minor=1, patch=3, prerelease=None)
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 3


class TestVersionRange:
    """Test VersionRange class functionality."""

    def test_exact_version_match(self):
        """Test exact version matching."""
        range_spec = VersionRange.parse("=2.1.3")
        version = ModelVersion(2, 1, 3)
        assert range_spec.is_compatible(version)

    def test_greater_than_version(self):
        """Test greater than version constraint."""
        range_spec = VersionRange.parse(">2.0.0")
        version = ModelVersion(2, 1, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 0, 0)
        assert not range_spec.is_compatible(version)

    def test_greater_than_or_equal_version(self):
        """Test greater than or equal version constraint."""
        range_spec = VersionRange.parse(">=2.0.0")
        version = ModelVersion(2, 0, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(1, 9, 0)
        assert not range_spec.is_compatible(version)

    def test_less_than_version(self):
        """Test less than version constraint."""
        range_spec = VersionRange.parse("<3.0.0")
        version = ModelVersion(2, 9, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(3, 0, 0)
        assert not range_spec.is_compatible(version)

    def test_less_than_or_equal_version(self):
        """Test less than or equal version constraint."""
        range_spec = VersionRange.parse("<=2.1.0")
        version = ModelVersion(2, 1, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 2, 0)
        assert not range_spec.is_compatible(version)

    def test_caret_range_compatible(self):
        """Test caret range (^) for compatible updates."""
        range_spec = VersionRange.parse("^2.1.3")
        # Compatible: >=2.1.3, <3.0.0
        version = ModelVersion(2, 1, 3)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 2, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 9, 9)
        assert range_spec.is_compatible(version)

        version = ModelVersion(3, 0, 0)
        assert not range_spec.is_compatible(version)

        version = ModelVersion(2, 1, 2)
        assert not range_spec.is_compatible(version)

    def test_tilde_range_patch_updates(self):
        """Test tilde range (~) for patch-only updates."""
        range_spec = VersionRange.parse("~2.1.3")
        # Patch updates only: >=2.1.3, <2.2.0
        version = ModelVersion(2, 1, 3)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 1, 5)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 2, 0)
        assert not range_spec.is_compatible(version)

        version = ModelVersion(2, 1, 2)
        assert not range_spec.is_compatible(version)

    def test_wildcard_range_any_version(self):
        """Test wildcard (*) for any version."""
        range_spec = VersionRange.parse("*")
        version = ModelVersion(1, 0, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(99, 99, 99)
        assert range_spec.is_compatible(version)

    def test_hyphen_range_between_versions(self):
        """Test hyphen range for version span."""
        range_spec = VersionRange.parse("2.0.0 - 2.5.0")
        version = ModelVersion(2, 0, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 3, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(2, 5, 0)
        assert range_spec.is_compatible(version)

        version = ModelVersion(1, 9, 0)
        assert not range_spec.is_compatible(version)

        version = ModelVersion(2, 6, 0)
        assert not range_spec.is_compatible(version)

    def test_invalid_version_string(self):
        """Test parsing invalid version string."""
        with pytest.raises(ValueError):
            ModelVersion.parse("invalid")

    def test_invalid_version_range_string(self):
        """Test parsing invalid version range string."""
        with pytest.raises(ValueError):
            VersionRange.parse("invalid")
