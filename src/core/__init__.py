"""
Core module for edge detection toolkit
Contains configuration management, error handling, and core utilities
"""

from .errors import EdgeDetectionError, ErrorCode, ErrorHandler
from .config import ConfigManager

__all__ = [
    'EdgeDetectionError',
    'ErrorCode',
    'ErrorHandler',
    'ConfigManager'
]
