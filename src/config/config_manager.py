"""
Configuration manager for edge-detection toolkit.

Loads configuration from YAML files and environment variables.
Supports nested configuration access with dot notation.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from .defaults import DEFAULT_CONFIG, get_default_config_path
from .validation import validate_config, EdgeDetectionConfig
from .profile_manager import ProfileManager


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ConfigManager:
    """
    Manages configuration loading and access.

    Configuration priority (highest to lowest):
    1. Environment variables (EDGE_DETECTION_*)
    2. User config file (~/.config/edge-detection/config.yaml)
    3. Project config file (./config/config.yaml)
    4. Default values

    Usage:
        config = ConfigManager()
        config.load()
        model_path = config.get('model.path')
    """

    def __init__(self, profile: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            profile: Optional profile name to load (dev, prod, testing).
        """
        self._config: Dict[str, Any] = {}
        self._loaded = False
        self._config_paths = []
        self._profile = profile
        self._profile_manager = ProfileManager(Path('./config'))

    def load(self, config_path: Optional[str] = None, skip_validation: bool = False) -> None:
        """
        Load configuration from file and environment variables.

        Args:
            config_path: Optional path to configuration file.
                        If not specified, searches default locations.
            skip_validation: If True, skip configuration validation.

        Raises:
            ConfigurationError: If configuration file cannot be loaded or is invalid.
        """
        # Start with defaults
        self._config = DEFAULT_CONFIG.copy()

        # Load profile if specified
        if self._profile:
            try:
                self._config = self._profile_manager.merge_with_profile(
                    self._config,
                    self._profile
                )
                logger.info(f"Loaded profile: {self._profile}")
            except FileNotFoundError as e:
                raise ConfigurationError(str(e)) from e

        # Load project config if exists
        project_config = Path('./config/config.yaml')
        if project_config.exists():
            self._load_yaml_file(project_config)

        # Load user config if exists
        if config_path:
            self._load_yaml_file(Path(config_path))
        else:
            user_config = get_default_config_path() / 'config.yaml'
            if user_config.exists():
                self._load_yaml_file(user_config)

        # Apply environment variable overrides
        self._apply_env_overrides()

        self._loaded = True

        # Validate configuration
        if not skip_validation:
            self.validate()

        logger.info(f"Configuration loaded successfully from {len(self._config_paths)} source(s)")

    def _load_yaml_file(self, config_path: Path) -> None:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file.

        Raises:
            ConfigurationError: If YAML file is invalid.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)

            if user_config:
                self._merge_config(self._config, user_config)
                self._config_paths.append(str(config_path))
                logger.debug(f"Loaded configuration from {config_path}")
        except yaml.YAMLError as e:
            error_line = getattr(e.problem_mark, 'line', 'unknown')
            error_col = getattr(e.problem_mark, 'column', 'unknown')
            raise ConfigurationError(
                f"Invalid YAML syntax in {config_path} at line {error_line}, column {error_col}\n"
                f"Error: {e}\n"
                f"Common fixes:\n"
                f"  - Check indentation (use spaces, not tabs)\n"
                f"  - Ensure colons (:) after keys\n"
                f"  - Quote strings with special characters\n"
                f"  - Check for unmatched brackets"
            ) from e
        except FileNotFoundError as e:
            # If file doesn't exist, that's okay - just skip it
            logger.debug(f"Configuration file not found: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}") from e

    def _merge_config(self, base: Dict, update: Dict) -> None:
        """
        Recursively merge update dict into base dict.

        Args:
            base: Base configuration dictionary (modified in place).
            update: Update dictionary to merge into base.
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides to configuration.

        Environment variables should follow naming convention:
        EDGE_DETECTION_<SECTION>_<KEY> for nested values.
        Use double underscore __ for nested keys.

        Examples:
            EDGE_DETECTION_MODEL__PATH -> model.path
            EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD -> detection.confidence_threshold
        """
        env_prefix = 'EDGE_DETECTION_'
        env_overrides = {}

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Remove prefix and convert to config key
                config_key = key[len(env_prefix):].lower().replace('__', '.')
                env_overrides[config_key] = value

        if env_overrides:
            logger.debug(f"Applying {len(env_overrides)} environment variable override(s)")
            for key, value in env_overrides.items():
                self._set_nested_value(self._config, key, value)
                logger.debug(f"  {key} = {value}")

    def _set_nested_value(self, config: Dict, key: str, value: str) -> None:
        """
        Set nested configuration value using dot notation.

        Args:
            config: Configuration dictionary.
            key: Dot-separated key path (e.g., 'model.path').
            value: Value to set (will be type-converted).
        """
        keys = key.split('.')
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Type convert the value
        final_key = keys[-1]
        current[final_key] = self._convert_type(value)

    def _convert_type(self, value: str) -> Any:
        """
        Convert string value to appropriate type.

        Args:
            value: String value to convert.

        Returns:
            Converted value (int, float, bool, or string).
        """
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Dot-separated configuration key (e.g., 'model.path').
            default: Default value if key not found.

        Returns:
            Configuration value or default.

        Raises:
            ConfigurationError: If configuration is not loaded.
        """
        if not self._loaded:
            raise ConfigurationError("Configuration not loaded. Call load() first.")

        keys = key.split('.')
        current = self._config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            if default is not None:
                logger.warning(f"Configuration key '{key}' not found, using default: {default}")
            return default

    def get_all(self) -> Dict[str, Any]:
        """
        Get complete configuration dictionary.

        Returns:
            Full configuration dictionary.

        Raises:
            ConfigurationError: If configuration is not loaded.
        """
        if not self._loaded:
            raise ConfigurationError("Configuration not loaded. Call load() first.")

        return self._config.copy()

    def validate(self) -> bool:
        """
        Validate configuration values using Pydantic schema.

        Returns:
            True if configuration is valid.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if not self._loaded:
            raise ConfigurationError("Configuration not loaded. Call load() first.")

        try:
            # Use Pydantic for comprehensive validation
            validate_config(self._config)
            logger.debug("Configuration validation passed")
            return True
        except ValueError as e:
            raise ConfigurationError(str(e)) from e
