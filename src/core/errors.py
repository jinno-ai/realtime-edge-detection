"""
Comprehensive error handling framework for edge detection toolkit

Provides:
- Custom exceptions with error codes
- Retry logic with exponential backoff
- Device fallback mechanism
- Error message templates with resolution hints
- Comprehensive exception handling with stack traces
"""
import time
import traceback
import logging
from enum import Enum
from typing import Optional, Callable, Any, TypeVar
from functools import wraps

from src.device.device_manager import DeviceManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Error Codes (AC: #5)
# ============================================================================

class ErrorCode(Enum):
    """
    Error codes for different types of errors

    Per story requirements:
    E001: MODEL_LOAD_FAILED
    E002: INVALID_IMAGE
    E003: DEVICE_ERROR
    E004: INFERENCE_FAILED
    E005: OUT_OF_MEMORY
    E006: INVALID_CONFIG
    """
    MODEL_LOAD_FAILED = "E001"
    INVALID_IMAGE = "E002"
    DEVICE_ERROR = "E003"
    INFERENCE_FAILED = "E004"
    OUT_OF_MEMORY = "E005"
    INVALID_CONFIG = "E006"


# ============================================================================
# Custom Exceptions
# ============================================================================

class EdgeDetectionError(Exception):
    """
    Base exception with error code, resolution hint, and stack trace

    Attributes:
        code: ErrorCode enum value
        hint: Resolution hint for the user
        original_exception: Original exception that caused this error
        stack_trace: Stack trace (only in debug mode)
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        hint: str = "",
        original_exception: Optional[Exception] = None,
        stack_trace: Optional[str] = None
    ):
        self.code = code
        self.hint = hint
        self.original_exception = original_exception
        self.stack_trace = stack_trace
        super().__init__(f"[{code.value}] {message}")

    def __str__(self) -> str:
        msg = super().__str__()
        if self.hint:
            msg += f"\n💡 Hint: {self.hint}"
        return msg


class RetryableError(EdgeDetectionError):
    """
    Error that can be retried (transient errors)

    Attributes:
        transient: Whether this error is transient (can be retried)
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        hint: str = "",
        transient: bool = True
    ):
        self.transient = transient
        super().__init__(code, message, hint)

    def can_retry(self) -> bool:
        """Check if this error can be retried"""
        return self.transient


# ============================================================================
# Retry Logic with Exponential Backoff (AC: #2)
# ============================================================================

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    backoff_intervals: Optional[list[float]] = None,
    debug_mode: bool = False
) -> T:
    """
    Retry function with exponential backoff for transient errors

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        backoff_intervals: Custom backoff intervals (defaults to [1, 2, 4] seconds)
        debug_mode: Enable debug logging

    Returns:
        Function result if successful

    Raises:
        RetryableError: If all retries fail
        EdgeDetectionError: If non-retryable error occurs

    Implementation:
        - Transient errors: 3 retries
        - Backoff: 1s, 2s, 4s (exponential)
        - Permanent errors: No retry
    """
    if backoff_intervals is None:
        backoff_intervals = [1.0, 2.0, 4.0]

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except RetryableError as e:
            last_error = e

            if not e.transient:
                # Permanent error, don't retry
                if debug_mode:
                    logger.debug(f"Permanent error encountered: {e}")
                raise

            if attempt < max_retries:
                # Get backoff interval (cycle through if more attempts than intervals)
                interval = backoff_intervals[min(attempt, len(backoff_intervals) - 1)]

                if debug_mode:
                    logger.debug(
                        f"Retry {attempt + 1}/{max_retries} after {interval}s delay. "
                        f"Error: {e}"
                    )

                time.sleep(interval)
            else:
                # All retries exhausted
                if debug_mode:
                    logger.debug(f"All {max_retries} retries exhausted. Last error: {e}")
                raise

        except Exception as e:
            # Non-retryable error
            raise

    # Should never reach here, but just in case
    if last_error:
        raise last_error


# ============================================================================
# Device Fallback Mechanism (AC: #1)
# ============================================================================

def with_device_fallback(preferred_device: Optional[str] = None):
    """
    Decorator that implements device fallback mechanism

    Fallback hierarchy:
    1. CUDA → CPU
    2. MPS → CPU
    3. TFLite → CPU

    Args:
        preferred_device: Preferred device to use first

    Example:
        @with_device_fallback(preferred_device="cuda:0")
        def detect_objects(device):
            # Detection logic
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            device_manager = DeviceManager()
            available_devices = device_manager.get_available_devices()

            # Determine device order based on preferred device
            if preferred_device and preferred_device in available_devices:
                device_order = [preferred_device]
            else:
                device_order = []

            # Add fallback devices
            for device in available_devices:
                if device not in device_order:
                    device_order.append(device)

            # Try each device in order
            last_error = None
            for device in device_order:
                try:
                    if debug_mode := kwargs.get('debug_mode', False):
                        logger.debug(f"Attempting detection on device: {device}")

                    result = func(device, *args, **kwargs)

                    # If we fell back from preferred device, log it
                    if device != preferred_device and preferred_device in device_order:
                        print(f"⚠️  {preferred_device} error, falling back to {device}")

                    return result

                except EdgeDetectionError as e:
                    last_error = e

                    # Only fallback on device errors
                    if e.code != ErrorCode.DEVICE_ERROR:
                        raise

                    if debug_mode := kwargs.get('debug_mode', False):
                        logger.debug(f"Device {device} failed: {e}")

                    # Try next device
                    continue

            # All devices failed
            if last_error:
                raise last_error

            # No devices available
            raise EdgeDetectionError(
                ErrorCode.DEVICE_ERROR,
                "No devices available for detection",
                hint=f"Available devices: {', '.join(available_devices) if available_devices else 'None'}. "
                     f"Use --device <device> to specify device"
            )

        return wrapper
    return decorator


# ============================================================================
# Error Handler with Recovery Strategies (AC: #1-6)
# ============================================================================

class ErrorHandler:
    """
    Centralized error handling with recovery strategies

    Provides:
    - User-friendly error messages
    - Resolution hints
    - Stack trace logging (debug mode only)
    - Bug report instructions
    """

    @staticmethod
    def handle(error: Exception, debug_mode: bool = False) -> None:
        """
        Handle error with logging and user-friendly message

        Args:
            error: Exception to handle
            debug_mode: Enable debug mode with stack traces
        """
        if isinstance(error, EdgeDetectionError):
            print(f"❌ {error}")
            if error.hint:
                print(f"💡 Hint: {error.hint}")

            # Log stack trace in debug mode
            if debug_mode and error.stack_trace:
                logger.debug(f"Stack trace:\n{error.stack_trace}")

        else:
            # Unexpected exception
            print(f"❌ Unexpected error: {error}")

            if debug_mode:
                stack_trace = traceback.format_exc()
                logger.debug(f"Stack trace:\n{stack_trace}")

    @staticmethod
    def create_error_message(
        code: ErrorCode,
        details: str,
        context: Optional[dict] = None
    ) -> tuple[str, str]:
        """
        Create error message with resolution hint based on error code

        Args:
            code: Error code
            details: Error details
            context: Additional context for creating specific messages

        Returns:
            Tuple of (error_message, resolution_hint)
        """
        # Error message templates (AC: #3-5)
        if code == ErrorCode.INVALID_IMAGE:
            message = f"Invalid image format: {details}. Supported formats: JPG, PNG, WEBP"
            hint = "Verify the image file is not corrupted"

        elif code == ErrorCode.INVALID_CONFIG:
            message = f"Configuration error: {details}"
            if context and 'parameter' in context:
                message = f"Invalid configuration parameter '{context['parameter']}': {details}"
            hint = "Check your configuration file syntax and parameter values"

        elif code == ErrorCode.OUT_OF_MEMORY:
            message = f"Out of memory. {details}"
            hint = "Try reducing batch size or using a smaller model"

        elif code == ErrorCode.DEVICE_ERROR:
            available_devices = context.get('available_devices', []) if context else []
            message = f"Device error: {details}"
            if available_devices:
                devices_str = ", ".join(available_devices)
                hint = f"Available devices: {devices_str}. Use --device <device> to specify device"
            else:
                hint = "No devices available. Check your hardware configuration"

        elif code == ErrorCode.MODEL_LOAD_FAILED:
            message = f"Failed to load model: {details}"
            hint = "Verify the model file exists and is compatible"

        elif code == ErrorCode.INFERENCE_FAILED:
            message = f"Inference failed: {details}"
            hint = "Check input data and model compatibility"

        else:
            message = f"Error: {details}"
            hint = "See documentation for troubleshooting"

        return message, hint

    @staticmethod
    def format_bug_report_instructions(error: Exception) -> str:
        """
        Create bug report instructions for unexpected errors

        Args:
            error: The exception that occurred

        Returns:
            Formatted bug report instructions
        """
        return (
            "This appears to be an unexpected error. "
            "Please consider filing a bug report at: "
            "https://github.com/jinno/realtime-edge-detection/issues"
        )


# ============================================================================
# Comprehensive Exception Handling Decorator (AC: #6)
# ============================================================================

def with_error_handling(func: Optional[Callable[..., T]] = None, *, debug_mode: bool = False):
    """
    Decorator for comprehensive exception handling

    Catches all exceptions and converts them to EdgeDetectionError
    with appropriate error codes and hints

    Args:
        func: Function to decorate (optional, for use with/without parentheses)
        debug_mode: Enable stack trace logging

    Example:
        @with_error_handling(debug_mode=True)
        def risky_function():
            # Function that might raise exceptions
            pass

        @with_error_handling
        def another_function():
            pass
    """
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @wraps(f)
        def wrapper(*args, **kwargs) -> T:
            try:
                return f(*args, **kwargs)

            except EdgeDetectionError:
                # Re-raise EdgeDetectionError as-is
                raise

            except Exception as e:
                # Convert unexpected exceptions to EdgeDetectionError
                stack_trace_str = traceback.format_exc() if debug_mode else None

                error = EdgeDetectionError(
                    ErrorCode.INFERENCE_FAILED,
                    f"Unexpected error in {f.__name__}: {str(e)}",
                    hint=ErrorHandler.format_bug_report_instructions(e),
                    original_exception=e,
                    stack_trace=stack_trace_str
                )

                # Log stack trace in debug mode
                if debug_mode:
                    logger.debug(f"Unexpected exception in {f.__name__}:\n{stack_trace_str}")

                raise error

        return wrapper

    # Support both @with_error_handling and @with_error_handling(debug_mode=True)
    if func is None:
        # Called with arguments: @with_error_handling(debug_mode=True)
        return decorator
    else:
        # Called without arguments: @with_error_handling
        return decorator(func)


# ============================================================================
# Convenience Functions
# ============================================================================

def create_model_load_error(details: str, **context) -> EdgeDetectionError:
    """Create model load error with appropriate message and hint"""
    message, hint = ErrorHandler.create_error_message(
        ErrorCode.MODEL_LOAD_FAILED,
        details,
        context
    )
    return EdgeDetectionError(ErrorCode.MODEL_LOAD_FAILED, message, hint)


def create_invalid_image_error(filename: str) -> EdgeDetectionError:
    """Create invalid image error with appropriate message and hint (AC: #3)"""
    message = f"Invalid image format: {filename}. Supported formats: JPG, PNG, WEBP"
    hint = "Verify the image file is not corrupted"
    return EdgeDetectionError(ErrorCode.INVALID_IMAGE, message, hint)


def create_device_error(details: str, available_devices: list = None) -> EdgeDetectionError:
    """Create device error with available devices hint (AC: #5)"""
    message, hint = ErrorHandler.create_error_message(
        ErrorCode.DEVICE_ERROR,
        details,
        {'available_devices': available_devices or []}
    )
    return EdgeDetectionError(ErrorCode.DEVICE_ERROR, message, hint)


def create_out_of_memory_error(batch_size: int, suggested_batch_size: int = None) -> EdgeDetectionError:
    """Create out of memory error with specific solution (AC: #4)"""
    if suggested_batch_size:
        message = f"Out of memory. Try reducing batch size from {batch_size} to {suggested_batch_size}"
    else:
        message = f"Out of memory with batch size {batch_size}"
    hint = "Try reducing batch size or using a smaller model"
    return EdgeDetectionError(ErrorCode.OUT_OF_MEMORY, message, hint)


def create_inference_error(details: str) -> EdgeDetectionError:
    """Create inference error with appropriate message and hint"""
    message, hint = ErrorHandler.create_error_message(
        ErrorCode.INFERENCE_FAILED,
        details
    )
    return EdgeDetectionError(ErrorCode.INFERENCE_FAILED, message, hint)
