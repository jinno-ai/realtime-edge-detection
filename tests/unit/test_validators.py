"""
Unit tests for configuration validation framework
Tests validation rules, error messages, and profile loading
"""
import pytest
from pathlib import Path

from src.core.validators import (
    ConfigValidator,
    ValidationError,
    ValidationRule,
    validate_config,
    list_validation_errors
)
from src.core.errors import EdgeDetectionError, ErrorCode


class TestConfigValidator:
    """Test ConfigValidator functionality"""

    def test_validator_initialization(self):
        """Test that validator initializes with all rules"""
        validator = ConfigValidator()
        assert len(validator.rules) > 0
        assert isinstance(validator.rules, list)

    def test_validate_valid_configuration(self):
        """Test validation passes for valid configuration"""
        validator = ConfigValidator()
        config = {
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4,
                'max_detections': 100,
                'batch_size': 1
            },
            'device': {
                'type': 'cpu'
            },
            'logging': {
                'level': 'INFO',
                'format': 'json'
            },
            'model': {
                'type': 'yolo_v8',
                'path': 'yolov8n.pt'
            }
        }

        errors = validator.validate(config)
        assert len(errors) == 0

    def test_validate_confidence_threshold_out_of_range_high(self):
        """Test validation catches confidence > 1.0"""
        validator = ConfigValidator()
        config = {
            'detection': {'confidence_threshold': 1.5}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'detection.confidence_threshold'
        assert '0.0' in errors[0].error and '1.0' in errors[0].error

    def test_validate_confidence_threshold_out_of_range_low(self):
        """Test validation catches confidence < 0.0"""
        validator = ConfigValidator()
        config = {
            'detection': {'confidence_threshold': -0.5}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'detection.confidence_threshold'

    def test_validate_confidence_threshold_boundary_valid(self):
        """Test validation accepts boundary values (0.0 and 1.0)"""
        validator = ConfigValidator()

        # Test 0.0
        config = {'detection': {'confidence_threshold': 0.0}}
        errors = validator.validate(config)
        assert len(errors) == 0

        # Test 1.0
        config = {'detection': {'confidence_threshold': 1.0}}
        errors = validator.validate(config)
        assert len(errors) == 0

    def test_validate_iou_threshold_out_of_range(self):
        """Test validation catches IOU threshold out of range"""
        validator = ConfigValidator()
        config = {
            'detection': {'iou_threshold': 1.2}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'detection.iou_threshold'
        assert errors[0].value == 1.2

    def test_validate_max_detections_invalid(self):
        """Test validation catches invalid max_detections"""
        validator = ConfigValidator()

        # Test zero
        config = {'detection': {'max_detections': 0}}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'detection.max_detections'

        # Test negative
        config = {'detection': {'max_detections': -10}}
        errors = validator.validate(config)
        assert len(errors) == 1

    def test_validate_batch_size_invalid(self):
        """Test validation catches invalid batch_size"""
        validator = ConfigValidator()
        config = {
            'detection': {'batch_size': 0}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'detection.batch_size'

    def test_validate_device_type_invalid(self):
        """Test validation catches invalid device type"""
        validator = ConfigValidator()
        config = {
            'device': {'type': 'invalid_device'}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'device.type'
        assert 'auto' in errors[0].error or 'cpu' in errors[0].error

    def test_validate_device_type_valid_options(self):
        """Test validation accepts all valid device types"""
        validator = ConfigValidator()
        valid_devices = ['auto', 'cpu', 'cuda', 'cuda:0', 'mps', 'tpu', 'tflite', 'onnx']

        for device in valid_devices:
            config = {'device': {'type': device}}
            errors = validator.validate(config)
            # Should not have device type errors (may have other errors for missing params)
            device_errors = [e for e in errors if e.parameter == 'device.type']
            assert len(device_errors) == 0, f"Device type '{device}' should be valid"

    def test_validate_logging_level_invalid(self):
        """Test validation catches invalid log level"""
        validator = ConfigValidator()
        config = {
            'logging': {'level': 'INVALID'}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'logging.level'

    def test_validate_logging_level_valid_options(self):
        """Test validation accepts all valid log levels"""
        validator = ConfigValidator()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in valid_levels:
            config = {'logging': {'level': level}}
            errors = validator.validate(config)
            level_errors = [e for e in errors if e.parameter == 'logging.level']
            assert len(level_errors) == 0, f"Log level '{level}' should be valid"

    def test_validate_logging_format_invalid(self):
        """Test validation catches invalid log format"""
        validator = ConfigValidator()
        config = {
            'logging': {'format': 'xml'}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'logging.format'

    def test_validate_metrics_port_out_of_range(self):
        """Test validation catches port out of valid range"""
        validator = ConfigValidator()

        # Test too low
        config = {'metrics': {'port': 100}}
        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'metrics.port'

        # Test too high
        config = {'metrics': {'port': 70000}}
        errors = validator.validate(config)
        assert len(errors) == 1

    def test_validate_model_type_invalid(self):
        """Test validation catches invalid model type"""
        validator = ConfigValidator()
        config = {
            'model': {'type': 'yolov999'}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'model.type'

    def test_validate_model_path_valid_formats(self):
        """Test validation accepts valid model path formats"""
        validator = ConfigValidator()

        # File path
        config = {'model': {'path': 'yolov8n.pt'}}
        errors = validator.validate(config)
        path_errors = [e for e in errors if e.parameter == 'model.path']
        assert len(path_errors) == 0

        # URL
        config = {'model': {'path': 'https://example.com/model.pt'}}
        errors = validator.validate(config)
        path_errors = [e for e in errors if e.parameter == 'model.path']
        assert len(path_errors) == 0

    def test_validate_model_path_invalid(self):
        """Test validation catches invalid model path"""
        validator = ConfigValidator()
        config = {
            'model': {'path': ''}
        }

        errors = validator.validate(config)
        assert len(errors) == 1
        assert errors[0].parameter == 'model.path'

    def test_validate_skips_none_values(self):
        """Test validation skips parameters that are None"""
        validator = ConfigValidator()
        config = {
            'detection': {
                'confidence_threshold': None,
                'iou_threshold': None
            }
        }

        errors = validator.validate(config)
        # None values should not cause validation errors
        assert len(errors) == 0

    def test_validate_multiple_errors(self):
        """Test validation returns multiple errors"""
        validator = ConfigValidator()
        config = {
            'detection': {
                'confidence_threshold': 1.5,
                'iou_threshold': -0.5,
                'max_detections': 0
            }
        }

        errors = validator.validate(config)
        assert len(errors) == 3

    def test_validate_error_message_structure(self):
        """Test that validation errors have proper structure"""
        validator = ConfigValidator()
        config = {
            'detection': {'confidence_threshold': 1.5}
        }

        errors = validator.validate(config)
        assert len(errors) == 1

        error = errors[0]
        assert isinstance(error, ValidationError)
        assert error.parameter == 'detection.confidence_threshold'
        assert error.value == 1.5
        assert error.error  # Error message exists
        assert error.hint  # Hint exists


class TestValidationFunctions:
    """Test validation helper functions"""

    def test_validate_config_raises_on_error(self):
        """Test validate_config raises exception on invalid config"""
        config = {
            'detection': {'confidence_threshold': 1.5}
        }

        with pytest.raises(EdgeDetectionError) as exc_info:
            validate_config(config)

        assert exc_info.value.code == ErrorCode.INVALID_CONFIG
        assert 'confidence_threshold' in str(exc_info.value)

    def test_validate_config_passes_on_valid(self):
        """Test validate_config passes for valid config"""
        config = {
            'detection': {'confidence_threshold': 0.5},
            'model': {'type': 'yolo_v8', 'path': 'yolov8n.pt'},
            'device': {'type': 'cpu'},
            'logging': {'level': 'INFO', 'format': 'json'}
        }

        # Should not raise
        validate_config(config)

    def test_list_validation_errors(self):
        """Test list_validation_errors returns formatted errors"""
        config = {
            'detection': {
                'confidence_threshold': 1.5,
                'iou_threshold': -0.5
            }
        }

        errors = list_validation_errors(config)
        assert len(errors) == 2
        assert 'confidence_threshold' in errors[0]
        assert 'iou_threshold' in errors[1]
        assert '💡' in errors[0]  # Should include hint


class TestValidationEdgeCases:
    """Test edge cases and special scenarios"""

    def test_validate_with_empty_config(self):
        """Test validation with empty configuration"""
        validator = ConfigValidator()
        config = {}

        errors = validator.validate(config)
        # Empty config should have no errors (None values are skipped)
        assert len(errors) == 0

    def test_validate_with_partial_config(self):
        """Test validation with partial configuration"""
        validator = ConfigValidator()
        config = {
            'detection': {'confidence_threshold': 0.7}
        }

        errors = validator.validate(config)
        # Should only validate what's present
        assert len(errors) == 0

    def test_validate_with_nested_path_access(self):
        """Test validator correctly accesses nested paths"""
        validator = ConfigValidator()
        config = {
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4
            }
        }

        # Should access nested values correctly
        errors = validator.validate(config)
        assert len(errors) == 0

    def test_validate_type_handling(self):
        """Test validator handles different types correctly"""
        validator = ConfigValidator()

        # String instead of float
        config = {'detection': {'confidence_threshold': '0.5'}}
        errors = validator.validate(config)
        # Should reject string
        assert len(errors) >= 1

        # Float instead of int
        config = {'detection': {'batch_size': 4.5}}
        errors = validator.validate(config)
        # Should reject float for int field
        assert len(errors) >= 1


class TestValidationErrorDataclass:
    """Test ValidationError dataclass"""

    def test_validation_error_creation(self):
        """Test ValidationError can be created"""
        error = ValidationError(
            parameter='test.param',
            value='invalid',
            error='Invalid value',
            hint='Use valid value'
        )

        assert error.parameter == 'test.param'
        assert error.value == 'invalid'
        assert error.error == 'Invalid value'
        assert error.hint == 'Use valid value'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
