"""
Configuration management system for edge detection toolkit
Supports YAML files, environment variable overrides, and validation
"""
import os
import re
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

import yaml

from .errors import EdgeDetectionError, ErrorCode
from .validators import ConfigValidator, ValidationError


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manage configuration from YAML files and environment variables

    Supports:
    - YAML configuration file loading
    - Environment variable overrides (EDGE_DETECTION_* prefix)
    - Default configuration merging
    - Configuration validation
    - Dot-notation access to nested values
    """

    # Default configuration values
    DEFAULT_CONFIG = {
        'model': {
            'type': 'yolo_v8',
            'path': 'yolov8n.pt',
            'download': True,
            'cache_dir': '~/.cache/edge-detection'
        },
        'device': {
            'type': 'auto',
            'optimize': True,
            'quantization': None
        },
        'detection': {
            'confidence_threshold': 0.5,
            'iou_threshold': 0.4,
            'max_detections': 100,
            'batch_size': 1
        },
        'logging': {
            'level': 'INFO',
            'format': 'json',
            'file': None,
            'rotation': '10MB'
        },
        'metrics': {
            'enabled': True,
            'export': 'prometheus',
            'port': 9090
        }
    }

    # Required configuration parameters
    REQUIRED_PARAMS = [
        'model.type',
        'model.path'
    ]

    def __init__(self, config_path: Optional[str] = None, profile: Optional[str] = None,
                 default_config: Optional[str] = None):
        """
        Initialize config manager

        Args:
            config_path: Path to user configuration file (optional)
            profile: Configuration profile (dev/prod/testing) (optional)
            default_config: Path to default configuration file (optional)
        """
        self.config_path = config_path
        self.profile = profile
        self.default_config_path = default_config
        self._config: Dict[str, Any] = {}
        self._validation_errors: List[str] = []
        self.validator = ConfigValidator()

        # Determine config directory
        if config_path:
            self.config_dir = Path(config_path).parent
        elif default_config:
            self.config_dir = Path(default_config).parent
        else:
            # Default to project config directory
            self.config_dir = Path(__file__).parent.parent.parent / 'config'

    def load_config(self) -> Dict[str, Any]:
        """
        Load and merge configuration from YAML + env vars

        Returns:
            Complete configuration dictionary

        Raises:
            EdgeDetectionError: If configuration is invalid or profile not found
        """
        # Start with built-in defaults
        self._config = self._deep_copy(self.DEFAULT_CONFIG)

        # 1. Load default config file if provided
        if self.default_config_path:
            default_from_file = self._load_yaml_file(self.default_config_path)
            if default_from_file:
                self._merge_configs(self._config, default_from_file)

        # 2. Load user configuration
        if self.config_path and Path(self.config_path).exists():
            user_config = self._load_yaml_file(self.config_path)
            if user_config:
                self._merge_configs(self._config, user_config)
        elif self.config_path:
            # Config file specified but doesn't exist - use defaults
            logger.warning(f"Config file not found: {self.config_path}, using defaults")

        # 3. Load profile if specified
        if self.profile:
            profile_config = self._load_profile(self.profile)
            if profile_config:
                self._merge_configs(self._config, profile_config)

        # 4. Apply environment variable overrides (highest priority)
        env_overrides = self._load_env_overrides()
        if env_overrides:
            self._merge_configs(self._config, env_overrides)

        # 5. Validate FINAL configuration (after ALL merges including env vars)
        # This is critical to ensure env var overrides don't bypass validation
        self._validate_configuration()

        # 6. Final validation after all merges
        self._validate_required_params()

        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation key

        Args:
            key: Dot-notation key (e.g., 'model.path')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set config value by dot-notation key

        Args:
            key: Dot-notation key (e.g., 'model.path')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the final key
        config[keys[-1]] = value

    def validate(self) -> bool:
        """
        Validate configuration parameters

        Returns:
            True if configuration is valid, False otherwise
        """
        self._validation_errors = []

        # Use validator framework
        errors = self.validator.validate(self._config)

        # Convert ValidationError objects to strings
        for error in errors:
            error_msg = f"{error.parameter}: {error.error} (got {error.value})"
            self._validation_errors.append(error_msg)

        # Check for missing required parameters
        for param in self.REQUIRED_PARAMS:
            if self.get(param) is None:
                self._validation_errors.append(f"Required parameter missing: {param}")

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> list:
        """Get list of validation error messages"""
        return self._validation_errors

    def _load_yaml_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load YAML file using safe_load

        Args:
            file_path: Path to YAML file

        Returns:
            Configuration dictionary or None if error

        Raises:
            EdgeDetectionError: If YAML is invalid
        """
        try:
            with open(file_path, 'r') as f:
                # CRITICAL: Use safe_load to prevent code injection
                config = yaml.safe_load(f)

                if config is None:
                    return {}

                if not isinstance(config, dict):
                    raise EdgeDetectionError(
                        ErrorCode.INVALID_CONFIG,
                        f"Configuration file must contain a dictionary, got {type(config).__name__}",
                        hint="Ensure your YAML file contains top-level key-value pairs"
                    )

                return config

        except yaml.YAMLError as e:
            # Extract line number from error if available
            error_msg = str(e)
            line_info = ""

            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                if mark:
                    line_info = f" (line {mark.line + 1})"

            raise EdgeDetectionError(
                ErrorCode.INVALID_CONFIG,
                f"Invalid YAML syntax in {file_path}{line_info}",
                hint="Check indentation and ensure valid YAML structure"
            ) from e

        except FileNotFoundError as e:
            logger.warning(f"Configuration file not found: {file_path}")
            return None

        except Exception as e:
            raise EdgeDetectionError(
                ErrorCode.INVALID_CONFIG,
                f"Error loading configuration from {file_path}: {str(e)}",
                hint="Check file permissions and format"
            ) from e

    def _load_env_overrides(self) -> Dict[str, Any]:
        """
        Parse EDGE_DETECTION_* environment variables

        Returns:
            Dictionary of configuration overrides

        Environment variable format: EDGE_DETECTION_SECTION_KEY
        - First underscore after prefix separates SECTION from KEY
        - Underscores within KEY are preserved (not converted to dots)
        - Example: EDGE_DETECTION_MODEL_PATH -> model.path
        - Example: EDGE_DETECTION_DETECTION_BATCH_SIZE -> detection.batch_size
        - Example: EDGE_DETECTION_LOGGING_FILE -> logging.file
        """
        overrides = {}
        pattern = re.compile(r'^EDGE_DETECTION_(.+)$')

        for key, value in os.environ.items():
            match = pattern.match(key)
            if match:
                # Get the part after EDGE_DETECTION_
                env_key = match.group(1)

                # Convert to lowercase
                env_key = env_key.lower()

                # Split on FIRST underscore only
                # This gives us: section, nested_key
                parts = env_key.split('_', 1)
                if len(parts) == 2:
                    section, nested_key = parts
                    # nested_key may contain underscores (like batch_size)
                    # These are part of the actual config key name, so preserve them
                    config_key = f"{section}.{nested_key}"
                else:
                    # No underscore, just the section
                    config_key = env_key

                converted_value = self._convert_type(value)

                # Set nested value
                self._set_nested_value(overrides, config_key, converted_value)

        return overrides

    def list_profiles(self) -> List[str]:
        """
        Discover and list available configuration profiles

        Returns:
            List of profile names (sorted alphabetically)
        """
        profiles = []

        # Scan config directory for YAML files
        if self.config_dir.exists():
            for file in self.config_dir.glob("*.yaml"):
                # Skip default.yaml (base config)
                if file.name != "default.yaml":
                    profiles.append(file.stem)

        return sorted(profiles)

    def _load_profile(self, profile: str) -> Optional[Dict[str, Any]]:
        """
        Load profile configuration (dev/prod/testing)

        Args:
            profile: Profile name

        Returns:
            Profile configuration or None

        Raises:
            EdgeDetectionError: If profile file doesn't exist
        """
        profile_file = self.config_dir / f"{profile}.yaml"

        if not profile_file.exists():
            # Get available profiles for error message
            available = self.list_profiles()

            raise EdgeDetectionError(
                ErrorCode.INVALID_CONFIG,
                f"Profile '{profile}' not found at {profile_file}",
                hint=f"Available profiles: {', '.join(available) if available else 'None'}. "
                     f"See: {self.config_dir}/prod.yaml for example"
            )

        return self._load_yaml_file(str(profile_file))

    def _validate_configuration(self) -> None:
        """
        Validate configuration and raise exception if invalid

        Raises:
            EdgeDetectionError: If configuration is invalid
        """
        errors = self.validator.validate(self._config)

        if errors:
            # Raise first error with full details
            error = errors[0]
            raise EdgeDetectionError(
                ErrorCode.INVALID_CONFIG,
                f"Invalid {error.parameter}: {error.value} - {error.error}",
                hint=error.hint
            )

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override config into base config

        Args:
            base: Base configuration (modified in place)
            override: Override configuration
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_configs(base[key], value)
            else:
                # Override value
                base[key] = value

    def _validate_required_params(self) -> None:
        """Check for missing required parameters and log warnings"""
        for param in self.REQUIRED_PARAMS:
            if self.get(param) is None:
                logger.warning(f"Required parameter missing: {param}, using default")

    def _convert_type(self, value: str) -> Union[int, float, bool, str]:
        """
        Convert string value to appropriate type

        Args:
            value: String value from environment variable

        Returns:
            Converted value (int, float, bool, or str)
        """
        # Try bool first (since 'true' is truthy but we want bool)
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Try int
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """
        Set nested dictionary value using dot notation

        Args:
            config: Configuration dictionary (modified in place)
            key: Dot-notation key (e.g., 'model.path')
            value: Value to set
        """
        keys = key.split('.')
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """Create a deep copy of an object"""
        import copy
        return copy.deepcopy(obj)
