"""
Secret masking utilities for secure logging.

Masks sensitive information like API keys, passwords, and tokens
before logging or displaying.
"""

import re
from typing import Any, Dict, List


class SecretMasker:
    """Masks sensitive information in logs and config."""

    # Patterns to detect sensitive data
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'api-key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'apikey["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'credential["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'bearer\s+([a-zA-Z0-9\-._~+/]+=*)',
        r'aws_access_key_id["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'aws_secret_access_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
    ]

    # Keys to mask in dictionaries
    SENSITIVE_KEYS = [
        'password', 'passwd', 'pwd',
        'api_key', 'apikey', 'api-key',
        'secret', 'secret_key',
        'token', 'access_token',
        'credential', 'credentials',
        'auth', 'authorization',
        'aws_access_key_id', 'aws_secret_access_key',
        'private_key', 'private-key',
    ]

    def __init__(self, mask_char: str = '*', visible_chars: int = 4):
        """
        Initialize secret masker.

        Args:
            mask_char: Character to use for masking
            visible_chars: Number of characters to show at end
        """
        self.mask_char = mask_char
        self.visible_chars = visible_chars

    def mask_value(self, value: str) -> str:
        """
        Mask a sensitive value.

        Args:
            value: Value to mask

        Returns:
            Masked value with only last few characters visible
        """
        if not value or len(value) <= self.visible_chars:
            return self.mask_char * 8

        masked_length = len(value) - self.visible_chars
        return self.mask_char * masked_length + value[-self.visible_chars:]

    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive values in dictionary.

        Args:
            data: Dictionary to mask

        Returns:
            Dictionary with sensitive values masked
        """
        masked = {}

        for key, value in data.items():
            # Check if key is sensitive
            key_lower = key.lower()
            is_sensitive = any(
                sensitive_key in key_lower
                for sensitive_key in self.SENSITIVE_KEYS
            )

            if is_sensitive and isinstance(value, str):
                # Mask the value
                masked[key] = self.mask_value(value)
            elif isinstance(value, dict):
                # Recursively mask nested dictionaries
                masked[key] = self.mask_dict(value)
            elif isinstance(value, list):
                # Mask lists
                masked[key] = [
                    self.mask_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Keep as-is
                masked[key] = value

        return masked

    def mask_string(self, text: str) -> str:
        """
        Mask sensitive patterns in text.

        Args:
            text: Text to mask

        Returns:
            Text with sensitive patterns masked
        """
        masked_text = text

        for pattern in self.SENSITIVE_PATTERNS:
            # Find and replace sensitive patterns
            matches = re.finditer(pattern, masked_text, re.IGNORECASE)

            for match in matches:
                if match.groups():
                    sensitive_value = match.group(1)
                    masked_value = self.mask_value(sensitive_value)
                    masked_text = masked_text.replace(
                        match.group(0),
                        match.group(0).replace(sensitive_value, masked_value)
                    )

        return masked_text

    def mask_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask configuration dictionary for logging.

        Args:
            config: Configuration dictionary

        Returns:
            Masked configuration
        """
        return self.mask_dict(config)


def mask_logging_handler(record):
    """
    Logging filter to mask sensitive information.

    Args:
        record: Log record

    Returns:
        Modified log record with masked message
    """
    masker = SecretMasker()

    # Mask the message
    record.msg = masker.mask_string(str(record.msg))

    # Mask args if present
    if record.args:
        masked_args = tuple(
            masker.mask_string(str(arg)) if isinstance(arg, str) else arg
            for arg in record.args
        )
        record.args = masked_args

    return record


def get_safe_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get safe version of config for logging/display.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with sensitive values masked

    Example:
        >>> config = {
        ...     'model_path': 'yolov8n.pt',
        ...     'api_key': 'sk-1234567890abcdef',
        ...     'confidence': 0.5
        ... }
        >>> safe_config = get_safe_config(config)
        >>> print(safe_config)
        {'model_path': 'yolov8n.pt', 'api_key': '******cdef', 'confidence': 0.5}
    """
    masker = SecretMasker()
    return masker.mask_config(config)


class SecureLogger:
    """Logger with automatic secret masking."""

    def __init__(self, logger, mask_char: str = '*'):
        """
        Initialize secure logger.

        Args:
            logger: Logger instance to wrap
            mask_char: Character to use for masking
        """
        self.logger = logger
        self.masker = SecretMasker(mask_char=mask_char)

    def _mask_args(self, *args):
        """Mask logging arguments."""
        return tuple(
            self.masker.mask_string(str(arg)) if isinstance(arg, str) else arg
            for arg in args
        )

    def info(self, msg, *args, **kwargs):
        """Log info message with masking."""
        masked_msg = self.masker.mask_string(str(msg))
        masked_args = self._mask_args(*args)
        self.logger.info(masked_msg, *masked_args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Log debug message with masking."""
        masked_msg = self.masker.mask_string(str(msg))
        masked_args = self._mask_args(*args)
        self.logger.debug(masked_msg, *masked_args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log warning message with masking."""
        masked_msg = self.masker.mask_string(str(msg))
        masked_args = self._mask_args(*args)
        self.logger.warning(masked_msg, *masked_args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log error message with masking."""
        masked_msg = self.masker.mask_string(str(msg))
        masked_args = self._mask_args(*args)
        self.logger.error(masked_msg, *masked_args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log critical message with masking."""
        masked_msg = self.masker.mask_string(str(msg))
        masked_args = self._mask_args(*args)
        self.logger.critical(masked_msg, *masked_args, **kwargs)
