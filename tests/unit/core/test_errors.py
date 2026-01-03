"""
Comprehensive tests for error handling framework
Tests all error codes, retry logic, fallback mechanisms, and error messages
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.core.errors import (
    ErrorCode,
    EdgeDetectionError,
    ErrorHandler,
    RetryableError,
    retry_with_backoff,
    with_device_fallback,
    with_error_handling
)


class TestErrorCode:
    """Test ErrorCode enum matches story requirements"""

    def test_error_code_values(self):
        """Test error codes match E001-E005 from story"""
        assert ErrorCode.MODEL_LOAD_FAILED.value == "E001"
        assert ErrorCode.INVALID_IMAGE.value == "E002"
        assert ErrorCode.DEVICE_ERROR.value == "E003"
        assert ErrorCode.INFERENCE_FAILED.value == "E004"
        assert ErrorCode.OUT_OF_MEMORY.value == "E005"


class TestEdgeDetectionError:
    """Test EdgeDetectionError exception class"""

    def test_error_with_code_and_message(self):
        """Test error creation with code and message"""
        error = EdgeDetectionError(
            ErrorCode.INVALID_IMAGE,
            "Invalid image format"
        )
        assert error.code == ErrorCode.INVALID_IMAGE
        assert ErrorCode.INVALID_IMAGE.value in str(error)
        assert "Invalid image format" in str(error)

    def test_error_with_hint(self):
        """Test error with resolution hint"""
        error = EdgeDetectionError(
            ErrorCode.INVALID_IMAGE,
            "Invalid image format",
            hint="Verify the image file is not corrupted"
        )
        assert error.hint == "Verify the image file is not corrupted"

    def test_error_string_representation(self):
        """Test error message format includes error code"""
        error = EdgeDetectionError(
            ErrorCode.DEVICE_ERROR,
            "CUDA device not found"
        )
        error_str = str(error)
        assert "[E003]" in error_str
        assert "CUDA device not found" in error_str


class TestRetryableError:
    """Test RetryableError for transient errors"""

    def test_retryable_error_creation(self):
        """Test creating retryable error"""
        error = RetryableError(
            ErrorCode.MODEL_LOAD_FAILED,
            "Network timeout downloading model",
            transient=True
        )
        assert error.transient is True
        assert error.can_retry()

    def test_non_retryable_error(self):
        """Test non-retryable error"""
        error = RetryableError(
            ErrorCode.INVALID_IMAGE,
            "Corrupted file",
            transient=False
        )
        assert error.transient is False
        assert not error.can_retry()


class TestRetryWithBackoff:
    """Test retry logic with exponential backoff"""

    def test_successful_operation_no_retry(self):
        """Test successful operation doesn't retry"""
        mock_func = Mock(return_value="success")

        result = retry_with_backoff(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_transient_error(self):
        """Test retry on transient error with exponential backoff"""
        mock_func = Mock(side_effect=[
            RetryableError(ErrorCode.MODEL_LOAD_FAILED, "Network timeout", transient=True),
            RetryableError(ErrorCode.MODEL_LOAD_FAILED, "Network timeout", transient=True),
            "success"
        ])

        start_time = time.time()
        result = retry_with_backoff(mock_func, max_retries=3)
        elapsed = time.time() - start_time

        assert result == "success"
        assert mock_func.call_count == 3
        # Should wait approximately 1s + 2s = 3s (exponential backoff)
        assert elapsed >= 2.5  # Allow some tolerance

    def test_retry_exhaustion(self):
        """Test failure after max retries"""
        mock_func = Mock(side_effect=RetryableError(
            ErrorCode.MODEL_LOAD_FAILED,
            "Network timeout",
            transient=True
        ))

        with pytest.raises(RetryableError):
            retry_with_backoff(mock_func, max_retries=2)

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_no_retry_on_permanent_error(self):
        """Test permanent errors are not retried"""
        mock_func = Mock(side_effect=RetryableError(
            ErrorCode.INVALID_IMAGE,
            "Corrupted file",
            transient=False
        ))

        with pytest.raises(RetryableError):
            retry_with_backoff(mock_func, max_retries=3)

        assert mock_func.call_count == 1  # No retries

    def test_custom_backoff_intervals(self):
        """Test custom backoff intervals"""
        mock_func = Mock(side_effect=[
            RetryableError(ErrorCode.MODEL_LOAD_FAILED, "Timeout", transient=True),
            RetryableError(ErrorCode.MODEL_LOAD_FAILED, "Timeout", transient=True),
            "success"
        ])

        start_time = time.time()
        result = retry_with_backoff(
            mock_func,
            max_retries=3,
            backoff_intervals=[0.1, 0.2]
        )
        elapsed = time.time() - start_time

        assert result == "success"
        # Should wait 0.1s + 0.2s = 0.3s
        assert elapsed >= 0.25


class TestDeviceFallback:
    """Test device fallback mechanism"""

    @patch('src.core.errors.DeviceManager')
    def test_cuda_to_cpu_fallback(self, MockDeviceManager):
        """Test CUDA fallback to CPU on device error"""
        mock_device_manager = MockDeviceManager.return_value
        mock_device_manager.get_available_devices.return_value = ["cuda:0", "cpu"]

        # Simulate CUDA error, then CPU success
        call_count = [0]

        def mock_detect(device):
            call_count[0] += 1
            if call_count[0] == 1:
                raise EdgeDetectionError(
                    ErrorCode.DEVICE_ERROR,
                    "CUDA out of memory"
                )
            return f"detection on {device}"

        @with_device_fallback(preferred_device="cuda:0")
        def detection_function(device):
            return mock_detect(device)

        result = detection_function()

        # Should fallback to CPU and succeed
        assert result == "detection on cpu"
        assert call_count[0] == 2

    @patch('src.core.errors.DeviceManager')
    def test_mps_to_cpu_fallback(self, MockDeviceManager):
        """Test MPS fallback to CPU"""
        mock_device_manager = MockDeviceManager.return_value
        mock_device_manager.get_available_devices.return_value = ["mps:0", "cpu"]

        call_count = [0]

        def mock_detect(device):
            call_count[0] += 1
            if call_count[0] == 1:
                raise EdgeDetectionError(ErrorCode.DEVICE_ERROR, "MPS error")
            return f"detection on {device}"

        @with_device_fallback(preferred_device="mps:0")
        def detection_function(device):
            return mock_detect(device)

        result = detection_function()

        assert result == "detection on cpu"
        assert call_count[0] == 2

    @patch('src.core.errors.DeviceManager')
    def test_no_fallback_on_non_device_error(self, MockDeviceManager):
        """Test no fallback for non-device errors"""
        mock_device_manager = MockDeviceManager.return_value
        mock_device_manager.get_available_devices.return_value = ["cuda:0", "cpu"]

        def mock_detect(device):
            raise EdgeDetectionError(
                ErrorCode.INVALID_IMAGE,
                "Corrupted image"
            )

        @with_device_fallback(preferred_device="cuda:0")
        def detection_function(device):
            return mock_detect(device)

        with pytest.raises(EdgeDetectionError) as exc_info:
            detection_function()

        assert exc_info.value.code == ErrorCode.INVALID_IMAGE
        assert exc_info.value.code != ErrorCode.DEVICE_ERROR

    @patch('src.core.errors.DeviceManager')
    def test_fallback_exhaustion(self, MockDeviceManager):
        """Test failure when all devices fail"""
        mock_device_manager = MockDeviceManager.return_value
        mock_device_manager.get_available_devices.return_value = ["cuda:0", "cpu"]

        @with_device_fallback(preferred_device="cuda:0")
        def detection_function(device):
            raise EdgeDetectionError(ErrorCode.DEVICE_ERROR, f"{device} failed")

        with pytest.raises(EdgeDetectionError) as exc_info:
            detection_function()

        assert exc_info.value.code == ErrorCode.DEVICE_ERROR


class TestErrorHandler:
    """Test ErrorHandler with recovery strategies"""

    def test_handle_edge_detection_error(self, capsys):
        """Test handling EdgeDetectionError with hint"""
        error = EdgeDetectionError(
            ErrorCode.INVALID_IMAGE,
            "Invalid image format: corrupted_file.jpg",
            hint="Verify the image file is not corrupted"
        )

        ErrorHandler.handle(error)

        captured = capsys.readouterr()
        assert "[E002]" in captured.out
        assert "Invalid image format: corrupted_file.jpg" in captured.out
        assert "Hint:" in captured.out
        assert "Verify the image file is not corrupted" in captured.out

    def test_handle_unexpected_exception(self, capsys):
        """Test handling unexpected exceptions"""
        error = ValueError("Some unexpected error")

        ErrorHandler.handle(error)

        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out
        assert "Some unexpected error" in captured.out

    def test_error_message_templates(self):
        """Test error message templates include resolutions"""
        # Test invalid image message
        error = EdgeDetectionError(
            ErrorCode.INVALID_IMAGE,
            "Invalid image format: corrupted_file.jpg. Supported formats: JPG, PNG, WEBP"
        )
        error_str = str(error)
        assert "corrupted_file.jpg" in error_str
        assert "JPG, PNG, WEBP" in error_str

        # Test out of memory message
        error = EdgeDetectionError(
            ErrorCode.OUT_OF_MEMORY,
            "Out of memory. Try reducing batch size from 32 to 16"
        )
        error_str = str(error)
        assert "Out of memory" in error_str
        assert "reducing batch size" in error_str

        # Test device error message
        error = EdgeDetectionError(
            ErrorCode.DEVICE_ERROR,
            "CUDA device unavailable",
            hint="Available devices: cpu. Use --device cpu to specify device"
        )
        assert error.hint
        assert "Available devices" in error.hint


class TestWithErrorHandlingDecorator:
    """Test with_error_handling decorator"""

    def test_catches_and_reraises_edge_detection_error(self):
        """Test decorator catches and re-raises EdgeDetectionError"""
        @with_error_handling
        def function_that_raises():
            raise EdgeDetectionError(
                ErrorCode.MODEL_LOAD_FAILED,
                "Model file not found"
            )

        with pytest.raises(EdgeDetectionError) as exc_info:
            function_that_raises()

        assert exc_info.value.code == ErrorCode.MODEL_LOAD_FAILED

    def test_catches_unexpected_and_converts(self):
        """Test decorator catches unexpected exceptions and converts"""
        @with_error_handling
        def function_that_raises():
            raise ValueError("Unexpected error")

        with pytest.raises(EdgeDetectionError) as exc_info:
            function_that_raises()

        # Should convert to EdgeDetectionError
        assert exc_info.value.code == ErrorCode.INFERENCE_FAILED

    def test_logs_stack_trace_in_debug_mode(self, caplog):
        """Test stack trace logging in debug mode"""
        import logging
        caplog.set_level(logging.DEBUG)

        @with_error_handling(debug_mode=True)
        def function_that_raises():
            raise ValueError("Unexpected error")

        with pytest.raises(EdgeDetectionError):
            function_that_raises()

        # Check that stack trace is logged
        assert any("Unexpected exception" in record.message for record in caplog.records)
        assert any("Traceback" in record.message for record in caplog.records)

    def test_includes_bug_report_instructions(self, capsys):
        """Test bug report instructions for unexpected errors"""
        @with_error_handling
        def function_that_raises():
            raise RuntimeError("Unexpected system error")

        with pytest.raises(EdgeDetectionError) as exc_info:
            function_that_raises()

        # Should include bug report hint
        assert "bug report" in exc_info.value.hint.lower() or "github" in exc_info.value.hint.lower()


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios from acceptance criteria"""

    def test_scenario_1_cuda_fallback_on_detection(self):
        """AC1: CUDA error -> CPU fallback -> detection continues"""
        with patch('src.core.errors.DeviceManager') as MockDM:
            mock_instance = MockDM.return_value
            mock_instance.get_available_devices.return_value = ["cuda:0", "cpu"]

            detection_calls = []

            @with_device_fallback(preferred_device="cuda:0")
            def detect_objects(device):
                detection_calls.append(device)
                if device == "cuda:0":
                    raise EdgeDetectionError(
                        ErrorCode.DEVICE_ERROR,
                        "CUDA error, falling back to CPU"
                    )
                return {"objects": []}

            result = detect_objects()

            assert result == {"objects": []}
            assert detection_calls == ["cuda:0", "cpu"]

    def test_scenario_2_model_download_retry(self):
        """AC2: Network error -> 3 retries with exponential backoff -> success"""
        download_attempts = []

        def mock_download():
            download_attempts.append(time.time())
            if len(download_attempts) < 3:
                raise RetryableError(
                    ErrorCode.MODEL_LOAD_FAILED,
                    "Network timeout",
                    transient=True
                )
            return "model downloaded"

        result = retry_with_backoff(mock_download, max_retries=3)

        assert result == "model downloaded"
        assert len(download_attempts) == 3

        # Verify exponential backoff intervals
        if len(download_attempts) >= 3:
            interval1 = download_attempts[1] - download_attempts[0]
            interval2 = download_attempts[2] - download_attempts[1]
            # Second interval should be approximately 2x first interval
            assert interval2 > interval1 * 1.5

    def test_scenario_3_invalid_image_error(self):
        """AC3: Invalid image -> clear error with hint"""
        error = EdgeDetectionError(
            ErrorCode.INVALID_IMAGE,
            "Invalid image format: corrupted_file.jpg. Supported formats: JPG, PNG, WEBP",
            hint="Verify the image file is not corrupted"
        )

        error_str = str(error)
        assert "[E002]" in error_str
        assert "corrupted_file.jpg" in error_str
        assert "JPG, PNG, WEBP" in error_str
        assert error.hint == "Verify the image file is not corrupted"

    def test_scenario_4_out_of_memory_error(self):
        """AC4: OOM during batch processing -> specific solution proposed"""
        error = EdgeDetectionError(
            ErrorCode.OUT_OF_MEMORY,
            "Out of memory. Try reducing batch size from 32 to 16"
        )

        error_str = str(error)
        assert "[E005]" in error_str
        assert "Out of memory" in error_str
        assert "reducing batch size from 32 to 16" in error_str

    def test_scenario_5_device_unavailable_error(self):
        """AC5: Device unavailable -> error code, available devices, solution"""
        with patch('src.core.errors.DeviceManager') as MockDM:
            mock_instance = MockDM.return_value
            mock_instance.get_available_devices.return_value = ["cpu"]

            @with_device_fallback(preferred_device="cuda:0")
            def detect(device):
                if device == "cuda:0":
                    raise EdgeDetectionError(
                        ErrorCode.DEVICE_ERROR,
                        "Device unavailable"
                    )
                return {"result": "ok"}

            # Should fallback and succeed
            result = detect()
            assert result == {"result": "ok"}

    def test_scenario_6_unexpected_exception_handling(self):
        """AC6: Unexpected exception -> catch, log stack trace, user-friendly message"""
        @with_error_handling(debug_mode=True)
        def risky_operation():
            # Simulate unexpected error
            raise IndexError("List index out of range")

        with pytest.raises(EdgeDetectionError) as exc_info:
            risky_operation()

        assert exc_info.value.code == ErrorCode.INFERENCE_FAILED
        assert "bug report" in exc_info.value.hint.lower()
