"""
Model management module for edge detection toolkit.

Provides automatic model download, caching, and validation.
"""

from .model_manager import ModelManager, ModelDownloadError, IntegrityError
from .base import AbstractDetector
from .onnx import ONNXDetector
from .onnx_converter import ONNXConverter, ONNXConversionError
from .onnx_optimizer import ONNXOptimizer
from .quantization import QuantizationPipeline, QuantizationFormat, QuantizationBackend
from .calibrator import Calibrator
from .accuracy_validator import AccuracyValidator

__all__ = [
    'ModelManager',
    'ModelDownloadError',
    'IntegrityError',
    'AbstractDetector',
    'ONNXDetector',
    'ONNXConverter',
    'ONNXConversionError',
    'ONNXOptimizer',
    'QuantizationPipeline',
    'QuantizationFormat',
    'QuantizationBackend',
    'Calibrator',
    'AccuracyValidator'
]
