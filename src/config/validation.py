"""
Configuration validation using Pydantic schemas.

Provides type-safe validation for all configuration parameters
with clear error messages and hints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Model configuration validation."""
    name: str = Field(default="yolov8n", description="Model name")
    path: Optional[str] = Field(default=None, description="Path to custom model file")
    cache_dir: str = Field(default="~/.cache/edge-detection/models", description="Model cache directory")

    @field_validator('name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model name."""
        valid_names = ['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x', 'yolov10n', 'yolov10s']
        v_lower = v.lower()
        if v_lower not in valid_names and v != 'custom':
            raise ValueError(
                f"Invalid model name: '{v}'. Must be one of {valid_names} or 'custom'"
            )
        return v_lower


class DeviceConfig(BaseModel):
    """Device configuration validation."""
    type: str = Field(default="auto", description="Device type")
    auto_detect: bool = Field(default=True, description="Auto-detect available devices")

    @field_validator('type')
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        """Validate device type."""
        valid_types = ['auto', 'cpu', 'cuda', 'mps', 'tpu', 'onnx']
        v_lower = v.lower()
        if v_lower not in valid_types and not v_lower.startswith('cuda:'):
            raise ValueError(
                f"Invalid device type: '{v}'. Must be one of {valid_types} or 'cuda:N'"
            )
        return v_lower


class DetectionConfig(BaseModel):
    """Detection parameters validation."""
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    max_detections: int = Field(default=300, ge=1, le=1000)


class InputConfig(BaseModel):
    """Input preprocessing validation."""
    image_size: List[int] = Field(default=[640, 640], description="Input image size [width, height]")
    letterbox: bool = Field(default=True, description="Use letterbox resizing")
    normalize: bool = Field(default=True, description="Normalize pixel values")

    @field_validator('image_size')
    @classmethod
    def validate_image_size(cls, v: List[int]) -> List[int]:
        """Validate image size."""
        if len(v) != 2:
            raise ValueError(f"image_size must have exactly 2 values, got {len(v)}")
        if any(dim <= 0 for dim in v):
            raise ValueError(f"image_size dimensions must be positive, got {v}")
        return v


class OutputConfig(BaseModel):
    """Output settings validation."""
    save_dir: str = Field(default="./output", description="Output directory")
    format: Literal['jpg', 'png'] = Field(default="jpg", description="Output format")
    show_confidence: bool = Field(default=True, description="Show confidence scores")
    show_labels: bool = Field(default=True, description="Show class labels")


class LoggingConfig(BaseModel):
    """Logging configuration validation."""
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default="INFO")
    format: Literal['text', 'json'] = Field(default="text")
    file: Optional[str] = Field(default=None, description="Log file path")


class PerformanceConfig(BaseModel):
    """Performance settings validation."""
    half_precision: bool = Field(default=False, description="Use FP16")
    batch_size: int = Field(default=1, ge=1, le=128)
    workers: int = Field(default=4, ge=1, le=16)


class EdgeDetectionConfig(BaseModel):
    """Complete configuration schema for edge detection toolkit."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    input: InputConfig = Field(default_factory=InputConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'allow'  # Allow extra fields for forward compatibility


def validate_config(config_dict: dict) -> EdgeDetectionConfig:
    """
    Validate configuration dictionary against schema.

    Args:
        config_dict: Configuration dictionary to validate.

    Returns:
        Validated EdgeDetectionConfig instance.

    Raises:
        ValueError: If configuration is invalid.
    """
    try:
        validated = EdgeDetectionConfig(**config_dict)
        logger.debug("Configuration validation passed")
        return validated
    except Exception as e:
        # Enhance error message with hints
        error_msg = str(e)
        hints = []

        # Add hints for common errors
        if 'confidence_threshold' in error_msg:
            hints.append("💡 Hint: confidence_threshold must be between 0.0 and 1.0")
        if 'iou_threshold' in error_msg:
            hints.append("💡 Hint: iou_threshold must be between 0.0 and 1.0")
        if 'device' in error_msg.lower():
            hints.append("💡 Hint: Valid device types: auto, cpu, cuda, mps, tpu, onnx")
        if 'model' in error_msg.lower():
            hints.append("💡 Hint: Valid model names: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x, yolov10n, yolov10s, custom")

        if hints:
            error_msg += '\n' + '\n'.join(hints)

        raise ValueError(error_msg) from e
