"""
Configuration management module for edge-detection toolkit.

Exports ConfigManager, validation schemas, and ProfileManager.
"""

from .config_manager import ConfigManager, ConfigurationError
from .validation import (
    EdgeDetectionConfig,
    ModelConfig,
    DeviceConfig,
    DetectionConfig,
    validate_config
)
from .profile_manager import ProfileManager

__all__ = [
    'ConfigManager',
    'ConfigurationError',
    'EdgeDetectionConfig',
    'ModelConfig',
    'DeviceConfig',
    'DetectionConfig',
    'validate_config',
    'ProfileManager',
]
