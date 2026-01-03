"""
Error handling framework for edge detection toolkit
Provides structured exceptions with error codes and resolution hints
"""
from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """Error codes for different types of errors"""
    INVALID_CONFIG = "E001"
    MODEL_LOAD_FAILED = "E002"
    INVALID_IMAGE = "E003"
    DEVICE_ERROR = "E004"
    INFERENCE_FAILED = "E005"
    VALIDATION_FAILED = "E006"
    INCOMPATIBLE_MODEL = "E007"


class EdgeDetectionError(Exception):
    """
    Base exception with error code and recovery hint

    Attributes:
        code: ErrorCode enum value
        hint: Resolution hint for the user
    """

    def __init__(self, code: ErrorCode, message: str, hint: str = ""):
        self.code = code
        self.hint = hint
        super().__init__(f"[{code.value}] {message}")


class ErrorHandler:
    """Centralized error handling"""

    @staticmethod
    def handle(error: Exception) -> None:
        """
        Handle error with logging and user-friendly message

        Args:
            error: Exception to handle
        """
        if isinstance(error, EdgeDetectionError):
            print(f"❌ {error}")
            if error.hint:
                print(f"💡 Hint: {error.hint}")
        else:
            print(f"❌ Unexpected error: {error}")
