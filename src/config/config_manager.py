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
        }
    }

    # Validation rules
    VALIDATION_RULES = {
        'detection.confidence_threshold': {
            'type': float,
            'min': 0.0,
            'max': 1.0
        },
        'detection.iou_threshold': {
            'type': float,
            'min': 0.0,
            'max': 1.0
        },
        'detection.max_detections': {
            'type': int,
            'min': 1,
            'max': 1000
        },
        'preprocessing.target_size': {
            'type': list,
            'min_length': 2,
            'max_length': 2
        },
        'device.type': {
            'type': str,
            'allowed_values': ['auto', 'cpu', 'cuda', 'mps', 'tpu', 'onnx']
        }
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
                print(f"⚠️  Profile '{self.profile}' not found. Using base configuration.")

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
        """Validate configuration values"""
        errors = []

        for key_path, rules in self.VALIDATION_RULES.items():
            section, key = key_path.split('.', 1)

            if section not in self.config:
                continue

            if key not in self.config[section]:
                continue

            value = self.config[section][key]

            # Type validation
            if 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    errors.append(
                        f"{key_path}: Expected type {expected_type.__name__}, got {type(value).__name__}"
                    )
                    continue

            # Range validation
            if 'min' in rules and value < rules['min']:
                errors.append(f"{key_path}: Value {value} is below minimum {rules['min']}")
            if 'max' in rules and value > rules['max']:
                errors.append(f"{key_path}: Value {value} is above maximum {rules['max']}")

            # Allowed values validation
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                errors.append(
                    f"{key_path}: Value '{value}' not in allowed values {rules['allowed_values']}"
                )

            # List length validation
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(f"{key_path}: List length {len(value)} is below minimum {rules['min_length']}")
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f"{key_path}: List length {len(value)} is above maximum {rules['max_length']}")

        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
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
