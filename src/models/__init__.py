"""
Model management module for edge detection toolkit.

Provides automatic model download, caching, and validation.
"""

from .model_manager import ModelManager, ModelDownloadError, IntegrityError

__all__ = ['ModelManager', 'ModelDownloadError', 'IntegrityError']
