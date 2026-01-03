"""
Configuration Manager for Edge Detection

Handles YAML configuration files with environment variable overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration data container"""
    model: Dict[str, Any]
    device: Dict[str, Any]
    detection: Dict[str, Any]
    preprocessing: Dict[str, Any]
    output: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model': self.model,
            'device': self.device,
            'detection': self.detection,
            'preprocessing': self.preprocessing,
            'output': self.output
        }


class ConfigManager:
    """
    Manages configuration from YAML files with environment variable overrides.

    Priority (highest to lowest):
    1. Environment variables (EDGE_DETECTION_<SECTION>_<KEY>)
    2. Profile-specific config (e.g., config/prod.yaml)
    3. Base config (config/default.yaml or ~/.config/edge-detection/config.yaml)
    4. Default values
    """

    # Default configuration values
    DEFAULT_CONFIG = {
        'model': {
            'path': 'yolov8n.pt',
            'auto_download': True,
            'cache_dir': '~/.cache/edge-detection/models'
        },
        'device': {
            'type': 'auto',  # auto, cpu, cuda, cuda:0, mps, etc.
            'fallback_to_cpu': True
        },
        'detection': {
            'confidence_threshold': 0.5,
            'iou_threshold': 0.4,
            'max_detections': 100
        },
        'preprocessing': {
            'target_size': [640, 640],
            'letterbox': True,
            'normalize': True
        },
        'output': {
            'format': 'json',  # json, csv, coco
            'save_detections': True,
            'output_dir': 'output'
        },
        'logging': {
            'level': 'INFO',
            'format': 'text',
            'file': None,
            'rotation': '10MB'
        },
        'metrics': {
            'enabled': True,
            'export': 'prometheus',
            'port': 9090
        }
    }

    # Validation rules (enhanced for Story 1.2)
    VALIDATION_RULES = {
        # Model settings
        'model.path': {
            'type': str,
            'required': True,
            'error_msg': 'Model path must be specified'
        },
        'model.auto_download': {
            'type': bool,
            'error_msg': 'auto_download must be a boolean (true/false)'
        },

        # Device settings
        'device.type': {
            'type': str,
            'allowed_values': ['auto', 'cpu', 'cuda', 'cuda:0', 'cuda:1', 'mps', 'tpu', 'onnx'],
            'error_msg': 'Device type must be one of: auto, cpu, cuda, cuda:0, cuda:1, mps, tpu, onnx'
        },

        # Detection settings
        'detection.confidence_threshold': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'error_msg': 'Confidence threshold must be between 0.0 and 1.0',
            'resolution_hint': 'Confidence threshold represents probability (0-100%). Valid values are between 0.0 and 1.0. Example: confidence_threshold: 0.5 (50% confidence)'
        },
        'detection.iou_threshold': {
            'type': float,
            'min': 0.0,
            'max': 1.0,
            'error_msg': 'IOU threshold must be between 0.0 and 1.0',
            'resolution_hint': 'IOU (Intersection over Union) threshold for Non-Maximum Suppression. Valid values are between 0.0 and 1.0. Example: iou_threshold: 0.4'
        },
        'detection.max_detections': {
            'type': int,
            'min': 1,
            'max': 1000,
            'error_msg': 'Max detections must be between 1 and 1000'
        },

        # Preprocessing
        'preprocessing.target_size': {
            'type': list,
            'min_length': 2,
            'max_length': 2,
            'element_type': int,
            'error_msg': 'Target size must be [width, height] with integer values'
        },
        'preprocessing.letterbox': {
            'type': bool,
            'error_msg': 'letterbox must be a boolean (true/false)'
        },
        'preprocessing.normalize': {
            'type': bool,
            'error_msg': 'normalize must be a boolean (true/false)'
        },

        # Output
        'output.format': {
            'type': str,
            'allowed_values': ['json', 'csv', 'coco'],
            'error_msg': 'Output format must be one of: json, csv, coco'
        },
        'output.save_detections': {
            'type': bool,
            'error_msg': 'save_detections must be a boolean (true/false)'
        },

        # Logging
        'logging.level': {
            'type': str,
            'allowed_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'error_msg': 'Logging level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL'
        },

        # Metrics
        'metrics.enabled': {
            'type': bool,
            'error_msg': 'metrics.enabled must be a boolean (true/false)'
        },
    }

    def __init__(self, config_path: Optional[str] = None, profile: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (YAML)
            profile: Profile name (dev, prod, testing) to load
        """
        self.config_path = config_path
        self.profile = profile
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load and merge configuration from multiple sources"""
        # Start with defaults
        self.config = self.DEFAULT_CONFIG.copy()

        # Load base config file
        base_config_path = self._find_config_file()
        if base_config_path:
            self._merge_yaml_file(base_config_path)

        # Load profile-specific config
        if self.profile:
            profile_config_path = self._find_profile_config(self.profile)
            if profile_config_path:
                self._merge_yaml_file(profile_config_path)
            else:
                available_profiles = self._list_available_profiles()
                profile_list = "\n".join(f"  • {name} - {desc}" for name, desc in sorted(available_profiles.items()))
                raise FileNotFoundError(
                    f"❌ Profile Not Found\n\n"
                    f"Profile '{self.profile}' does not exist.\n\n"
                    f"Available profiles:\n"
                    f"{profile_list}\n\n"
                    f"Profile location: config/{self.profile}.yaml\n\n"
                    f"To create a custom profile:\n"
                    f"  1. Copy config/default.yaml\n"
                    f"  2. Rename to config/{self.profile}.yaml\n"
                    f"  3. Modify settings as needed\n\n"
                    f"Example profile file location: config/prod.yaml"
                )

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Validate configuration
        self._validate_config()

    def _find_config_file(self) -> Optional[Path]:
        """
        Find configuration file in standard locations.

        Search order:
        1. Explicitly provided config_path
        2. ./config.yaml
        3. ./config/default.yaml
        4. ~/.config/edge-detection/config.yaml
        """
        if self.config_path:
            path = Path(self.config_path)
            if path.exists():
                return path
            else:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Check current directory
        local_config = Path.cwd() / 'config.yaml'
        if local_config.exists():
            return local_config

        # Check config/default.yaml
        default_config = Path.cwd() / 'config' / 'default.yaml'
        if default_config.exists():
            return default_config

        # Check user config directory
        user_config = Path.home() / '.config' / 'edge-detection' / 'config.yaml'
        if user_config.exists():
            return user_config

        return None

    def _find_profile_config(self, profile: str) -> Optional[Path]:
        """Find profile-specific configuration file"""
        profile_paths = [
            Path.cwd() / 'config' / f'{profile}.yaml',
            Path.home() / '.config' / 'edge-detection' / f'{profile}.yaml'
        ]

        for path in profile_paths:
            if path.exists():
                return path

        return None

    def _list_available_profiles(self) -> dict:
        """List all available profile configuration files with descriptions"""
        config_dir = Path.cwd() / 'config'
        profiles = {}

        # Profile descriptions
        profile_descriptions = {
            'dev': 'Development environment with debug logging',
            'prod': 'Production environment optimized for performance',
            'testing': 'Testing environment with deterministic settings'
        }

        if config_dir.exists():
            for profile_file in config_dir.glob('*.yaml'):
                # Skip default.yaml as it's the base config
                if profile_file.name != 'default.yaml':
                    profile_name = profile_file.stem
                    description = profile_descriptions.get(profile_name, 'Custom profile')
                    profiles[profile_name] = description

        # Also check user config directory
        user_config_dir = Path.home() / '.config' / 'edge-detection'
        if user_config_dir.exists():
            for profile_file in user_config_dir.glob('*.yaml'):
                profile_name = profile_file.stem
                if profile_name not in profiles:
                    profiles[profile_name] = 'Custom user profile'

        return profiles

    def _merge_yaml_file(self, file_path: Path) -> None:
        """Merge YAML file into configuration"""
        try:
            with open(file_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    self._deep_merge(self.config, yaml_config)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        env_prefix = 'EDGE_DETECTION_'

        for env_var, env_value in os.environ.items():
            if not env_var.startswith(env_prefix):
                continue

            # Parse EDGE_DETECTION_SECTION_KEY
            parts = env_var[len(env_prefix):].lower().split('_')
            if len(parts) < 2:
                continue

            section = parts[0]
            key = '_'.join(parts[1:])

            if section not in self.config:
                continue

            # Convert environment variable value to appropriate type
            self.config[section][key] = self._parse_env_value(env_value)

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Try integer
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

    def _validate_config(self) -> None:
        """Validate configuration values with enhanced error messages"""
        errors = []

        for key_path, rules in self.VALIDATION_RULES.items():
            parts = key_path.split('.')
            if len(parts) < 2:
                continue

            section = parts[0]
            key = '.'.join(parts[1:])

            if section not in self.config:
                continue

            if key not in self.config[section]:
                # Check if required
                if rules.get('required', False):
                    errors.append(f"{key_path}: {rules.get('error_msg', 'Required field is missing')}")
                continue

            value = self.config[section][key]

            # Type validation
            if 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    error_msg = rules.get('error_msg',
                        f"Invalid type for {key_path}: expected {expected_type.__name__}, got {type(value).__name__}")
                    errors.append(f"{key_path}: {error_msg}")
                    continue

            # Range validation with enhanced messages
            if 'min' in rules and value < rules['min']:
                error_msg = rules.get('error_msg',
                    f"{key_path} must be >= {rules['min']}")
                errors.append(f"{key_path}: {error_msg} (got: {value})")

                # Add resolution hint if available
                if 'resolution_hint' in rules:
                    errors.append(f"  Hint: {rules['resolution_hint']}")

            if 'max' in rules and value > rules['max']:
                error_msg = rules.get('error_msg',
                    f"{key_path} must be <= {rules['max']}")
                errors.append(f"{key_path}: {error_msg} (got: {value})")

                # Add resolution hint if available
                if 'resolution_hint' in rules:
                    errors.append(f"  Hint: {rules['resolution_hint']}")

            # Allowed values validation
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                error_msg = rules.get('error_msg',
                    f"Invalid value for {key_path}: {value}. Allowed: {rules['allowed_values']}")
                errors.append(f"{key_path}: {error_msg}")

            # List length validation
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(f"{key_path}: List length {len(value)} is below minimum {rules['min_length']}")
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f"{key_path}: List length {len(value)} is above maximum {rules['max_length']}")

            # List element type validation
            if 'element_type' in rules and isinstance(value, list):
                for i, elem in enumerate(value):
                    if not isinstance(elem, rules['element_type']):
                        errors.append(f"{key_path}: Element {i} has invalid type. Expected {rules['element_type'].__name__}")

        if errors:
            error_message = "❌ Configuration Validation Error\n\n" + "\n".join(f"  • {e}" for e in errors)
            error_message += "\n\n[✕] Failed to validate configuration. Fix the errors above and try again."
            raise ValueError(error_message)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Configuration section (e.g., 'model', 'device')
            key: Configuration key within section
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if section not in self.config:
            if default is not None:
                return default
            raise KeyError(f"Configuration section '{section}' not found")

        if key not in self.config[section]:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{section}.{key}' not found")

        return self.config[section][key]

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Configuration section name

        Returns:
            Dictionary containing all key-value pairs in section
        """
        if section not in self.config:
            raise KeyError(f"Configuration section '{section}' not found")

        return self.config[section].copy()

    def load_profile(self, profile_name: str) -> 'ConfigManager':
        """
        Load configuration profile and return a new ConfigManager instance.

        This is a convenience method that creates a new ConfigManager with the specified profile.

        Args:
            profile_name: Name of profile (dev, prod, testing)

        Returns:
            ConfigManager instance with profile loaded

        Raises:
            FileNotFoundError: If profile file doesn't exist
        """
        return ConfigManager(profile=profile_name)

    def to_dataclass(self) -> Config:
        """Convert configuration to Config dataclass"""
        return Config(
            model=self.config['model'],
            device=self.config['device'],
            detection=self.config['detection'],
            preprocessing=self.config['preprocessing'],
            output=self.config['output']
        )

    def save_default_config(self, output_path: str = 'config.yaml') -> None:
        """
        Save default configuration to YAML file.

        Args:
            output_path: Path to save configuration file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Default configuration saved to: {output_file}")

    def __repr__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(profile={self.profile}, sections={list(self.config.keys())})"
