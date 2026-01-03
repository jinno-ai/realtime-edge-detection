"""
Configuration validation framework for edge detection toolkit
Provides structured validation with clear error messages and hints
"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from .errors import EdgeDetectionError, ErrorCode


@dataclass
class ValidationRule:
    """
    Configuration validation rule

    Attributes:
        parameter_path: Dot-notation path (e.g., "detection.confidence_threshold")
        validator: Callable that returns True if value is valid
        error_message: Error message describing what's wrong
        hint: Resolution hint for the user
    """
    parameter_path: str
    validator: Callable[[Any], bool]
    error_message: str
    hint: str


@dataclass
class ValidationError:
    """
    Configuration validation error

    Attributes:
        parameter: Parameter path (dot notation)
        value: The invalid value
        error: Error message
        hint: Resolution hint
    """
    parameter: str
    value: Any
    error: str
    hint: str


class ConfigValidator:
    """
    Configuration validation engine

    Validates configuration parameters against defined rules and provides
    structured error messages with actionable hints.
    """

    def __init__(self):
        """Initialize validator with all validation rules"""
        self.rules = self._load_validation_rules()

    def validate(self, config: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate entire configuration dictionary

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for rule in self.rules:
            value = self._get_value(config, rule.parameter_path)

            # Skip validation if value is None (not set)
            # ConfigManager will handle required parameters
            if value is None:
                continue

            try:
                if not rule.validator(value):
                    errors.append(ValidationError(
                        parameter=rule.parameter_path,
                        value=value,
                        error=rule.error_message,
                        hint=rule.hint
                    ))
            except Exception as e:
                # Validator itself raised an error
                errors.append(ValidationError(
                    parameter=rule.parameter_path,
                    value=value,
                    error=f"Validation failed: {str(e)}",
                    hint=rule.hint
                ))

        return errors

    def _get_value(self, config: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from config using dot notation

        Args:
            config: Configuration dictionary
            path: Dot-notation path (e.g., "detection.confidence_threshold")

        Returns:
            Value at path or None if not found
        """
        keys = path.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _load_validation_rules(self) -> List[ValidationRule]:
        """
        Define all validation rules

        Returns:
            List of validation rules
        """
        rules = [
            # Detection parameters
            ValidationRule(
                parameter_path="detection.confidence_threshold",
                validator=lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                error_message="Confidence threshold must be between 0.0 and 1.0",
                hint="Set detection.confidence_threshold to a value in [0.0, 1.0]"
            ),
            ValidationRule(
                parameter_path="detection.iou_threshold",
                validator=lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                error_message="IOU threshold must be between 0.0 and 1.0",
                hint="Set detection.iou_threshold to a value in [0.0, 1.0]"
            ),
            # Issue #5: Reject float values for integer fields (bool is subclass of int in Python)
            ValidationRule(
                parameter_path="detection.max_detections",
                validator=lambda x: isinstance(x, int) and not isinstance(x, bool) and x >= 1,
                error_message="Max detections must be a positive integer (not float or boolean)",
                hint="Set detection.max_detections to an integer >= 1"
            ),
            ValidationRule(
                parameter_path="detection.batch_size",
                validator=lambda x: isinstance(x, int) and not isinstance(x, bool) and x >= 1,
                error_message="Batch size must be a positive integer (not float or boolean)",
                hint="Set detection.batch_size to an integer >= 1"
            ),

            # Device parameters
            # Issue #3: Added .lower() for case-insensitive device type validation
            ValidationRule(
                parameter_path="device.type",
                validator=lambda x: isinstance(x, str) and x.lower() in [
                    'auto', 'cpu', 'cuda', 'cuda:0', 'cuda:1', 'mps', 'tpu', 'tflite', 'onnx'
                ],
                error_message="Device type must be one of: auto, cpu, cuda, mps, tpu, tflite, onnx (case-insensitive)",
                hint="Set device.type to a supported device (auto, cpu, cuda, mps, tpu, tflite, onnx)"
            ),
            # Issue #6: Added validator for device.optimize (boolean)
            ValidationRule(
                parameter_path="device.optimize",
                validator=lambda x: isinstance(x, bool),
                error_message="Device optimize must be a boolean (true/false)",
                hint="Set device.optimize to true or false"
            ),
            # Issue #6: Added validator for device.quantization (null or string)
            ValidationRule(
                parameter_path="device.quantization",
                validator=lambda x: x is None or (isinstance(x, str) and x.lower() in ['int8', 'fp16']),
                error_message="Device quantization must be null or one of: int8, fp16",
                hint="Set device.quantization to null, 'int8', or 'fp16'"
            ),

            # Logging parameters
            # Issue #2: Logging level validator now case-insensitive (normalizes to uppercase)
            ValidationRule(
                parameter_path="logging.level",
                validator=lambda x: isinstance(x, str) and x.upper() in [
                    'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                ],
                error_message="Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive)",
                hint="Set logging.level to a valid log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
            ),
            ValidationRule(
                parameter_path="logging.format",
                validator=lambda x: isinstance(x, str) and x.lower() in ['text', 'json'],
                error_message="Log format must be either 'text' or 'json' (case-insensitive)",
                hint="Set logging.format to 'text' or 'json'"
            ),

            # Metrics parameters
            ValidationRule(
                parameter_path="metrics.port",
                validator=lambda x: isinstance(x, int) and not isinstance(x, bool) and 1024 <= x <= 65535,
                error_message="Metrics port must be between 1024 and 65535 (integer)",
                hint="Set metrics.port to a valid port number (1024-65535)"
            ),
            ValidationRule(
                parameter_path="metrics.export",
                validator=lambda x: isinstance(x, str) and x.lower() in ['prometheus', 'json', 'none'],
                error_message="Metrics export must be one of: prometheus, json, none (case-insensitive)",
                hint="Set metrics.export to 'prometheus', 'json', or 'none'"
            ),

            # Model parameters
            # Issue #7: Standardized on underscore naming convention (yolo_v8, yolov10)
            ValidationRule(
                parameter_path="model.type",
                validator=lambda x: isinstance(x, str) and x.lower() in [
                    'yolo_v8', 'yolov8', 'yolo_v10', 'yolov10', 'yolo_v5', 'yolov5'
                ],
                error_message="Model type must be one of: yolo_v8, yolov10, yolov5 (case-insensitive)",
                hint="Set model.type to a supported model (yolo_v8, yolov10, yolov5)"
            ),
            ValidationRule(
                parameter_path="model.path",
                validator=self._validate_model_path,
                error_message="Model path must be a valid file path or URL",
                hint="Set model.path to a valid file path or URL (e.g., 'yolov8n.pt' or 'https://example.com/model.pt')"
            ),
        ]

        return rules

    def _validate_model_path(self, path: Any) -> bool:
        """
        Validate model path (file path or URL)

        Args:
            path: Model path to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(path, str) or not path:
            return False

        # Check if it's a URL
        if path.startswith(('http://', 'https://', 'ftp://')):
            return True

        # Check if it's a file path (relative or absolute)
        # We don't check if the file exists, just if the path format is valid
        try:
            Path(path)
            return True
        except Exception:
            return False


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration and raise exception if invalid

    Args:
        config: Configuration dictionary to validate

    Raises:
        EdgeDetectionError: If configuration is invalid
    """
    validator = ConfigValidator()
    errors = validator.validate(config)

    if errors:
        # Raise first error with full details
        error = errors[0]
        raise EdgeDetectionError(
            ErrorCode.INVALID_CONFIG,
            f"Invalid {error.parameter}: {error.value} - {error.error}",
            hint=error.hint
        )


def list_validation_errors(config: Dict[str, Any]) -> List[str]:
    """
    Get human-readable list of validation errors

    Args:
        config: Configuration dictionary to validate

    Returns:
        List of error messages
    """
    validator = ConfigValidator()
    errors = validator.validate(config)

    messages = []
    for error in errors:
        msg = f"❌ {error.parameter} = {error.value}\n   {error.error}\n   💡 {error.hint}"
        messages.append(msg)

    return messages
