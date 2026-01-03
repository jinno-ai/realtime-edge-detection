"""
Profile management for configuration.

Handles loading and merging profile-based configurations.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages configuration profiles."""

    def __init__(self, config_dir: Path):
        """
        Initialize profile manager.

        Args:
            config_dir: Directory containing profile YAML files.
        """
        self.config_dir = Path(config_dir)

    def list_available_profiles(self) -> List[str]:
        """
        List all available profile files.

        Returns:
            List of profile names (without .yaml extension).
        """
        if not self.config_dir.exists():
            logger.warning(f"Config directory does not exist: {self.config_dir}")
            return []

        profiles = []
        for profile_file in self.config_dir.glob('*.yaml'):
            # Skip default.yaml as it's the base config
            if profile_file.name != 'default.yaml' and profile_file.name != 'example.yaml':
                profiles.append(profile_file.stem)

        return sorted(profiles)

    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Load profile configuration.

        Args:
            profile_name: Name of profile to load (without .yaml extension).

        Returns:
            Profile configuration dictionary.

        Raises:
            FileNotFoundError: If profile file does not exist.
            ValueError: If profile file is invalid.
        """
        profile_path = self.config_dir / f"{profile_name}.yaml"

        if not profile_path.exists():
            available = self.list_available_profiles()
            raise FileNotFoundError(
                f"Profile '{profile_name}' not found at {profile_path}\n"
                f"Available profiles: {', '.join(available) if available else '(none)'}\n"
                f"💡 Hint: Check config directory: {self.config_dir}\n"
                f"💡 Hint: Create profile file or use --profile with available profile"
            )

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_config = yaml.safe_load(f)

            if not isinstance(profile_config, dict):
                raise ValueError(
                    f"Profile file must contain a YAML dictionary, got {type(profile_config).__name__}"
                )

            logger.info(f"Loaded profile '{profile_name}' from {profile_path}")
            return profile_config

        except yaml.YAMLError as e:
            error_line = getattr(e.problem_mark, 'line', 'unknown')
            error_col = getattr(e.problem_mark, 'column', 'unknown')
            raise ValueError(
                f"Invalid YAML in profile '{profile_name}' at line {error_line}, column {error_col}\n"
                f"Error: {e}\n"
                f"💡 Hint: Check YAML syntax (indentation, colons, quotes)"
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to load profile '{profile_name}': {e}") from e

    def deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base configuration dictionary.
            override: Override dictionary to merge into base.

        Returns:
            Merged dictionary (new instance, original dicts not modified).
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def merge_with_profile(
        self,
        base_config: Dict[str, Any],
        profile_name: str
    ) -> Dict[str, Any]:
        """
        Merge base configuration with profile.

        Args:
            base_config: Base configuration dictionary.
            profile_name: Name of profile to merge.

        Returns:
            Merged configuration dictionary.

        Raises:
            FileNotFoundError: If profile does not exist.
        """
        profile_config = self.load_profile(profile_name)
        merged = self.deep_merge(base_config, profile_config)

        logger.debug(f"Merged profile '{profile_name}' into base configuration")
        return merged
