"""
Structured logging system with JSON and text format support
Provides production-ready logging with context tracking and log rotation
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, TextIO
from pathlib import Path
import os
import gzip
import shutil
import traceback


class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log entry
        """
        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add context if present
        if hasattr(record, 'context') and record.context:
            log_entry['context'] = record.context

        # Add metrics if present
        if hasattr(record, 'metrics') and record.metrics:
            log_entry['metrics'] = record.metrics

        # Add exception info if present
        if record.exc_info:
            log_entry['stack_trace'] = self.formatException(record.exc_info)

        # Add process/thread info
        log_entry['process_id'] = record.process
        log_entry['thread_id'] = record.thread

        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """Format log records as human-readable text"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text

        Args:
            record: Log record to format

        Returns:
            Text-formatted log entry
        """
        # Base message with timestamp and level
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        message = f"{timestamp} {record.levelname:8} [{record.name}] {record.getMessage()}"

        # Add context if present
        if hasattr(record, 'context') and record.context:
            context_str = ' '.join([f"{k}={v}" for k, v in record.context.items()])
            message += f"\n  context: {context_str}"

        # Add metrics if present
        if hasattr(record, 'metrics') and record.metrics:
            metrics_str = ' '.join([f"{k}={v}" for k, v in record.metrics.items()])
            message += f"\n  metrics: {metrics_str}"

        # Add exception info if present
        if record.exc_info:
            message += f"\n  stack_trace:\n{self.formatException(record.exc_info)}"

        return message


class StructuredLogger:
    """
    Structured logger with JSON/text format support and context tracking

    Features:
    - JSON and text log formats
    - Context information in logs
    - Metrics tracking
    - Automatic log rotation (10MB, max 5 files, compression)
    - Thread-safe logging
    - Millisecond precision timestamps

    Args:
        name: Logger name
        log_file: Path to log file (None for stdout only)
        format: Log format ('json' or 'text')
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum file size before rotation (default: 10MB)
        backup_count: Maximum number of backup files (default: 5)
        compress: Compress rotated logs with gzip (default: True)
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        format: str = 'json',
        level: str = 'INFO',
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        compress: bool = True
    ):
        """
        Initialize structured logger

        Args:
            name: Logger name
            log_file: Path to log file (None for stdout only)
            format: Log format ('json' or 'text')
            level: Log level
            max_bytes: Maximum file size before rotation
            backup_count: Maximum number of backup files
            compress: Compress rotated logs
        """
        self.name = name
        self.format = format
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress

        # Create logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper()))
        self._logger.handlers.clear()  # Remove existing handlers

        # Create formatter
        if format == 'json':
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()

        # Add file handler if log file specified
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Use RotatingFileHandler for automatic rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, level.upper()))
            self._logger.addHandler(file_handler)

            # Custom rotation for compression
            if compress:
                self._setup_compression(file_handler)

        # Add console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        self._logger.addHandler(console_handler)

        # Prevent propagation to root logger
        self._logger.propagate = False

    def _setup_compression(self, handler: logging.Handler) -> None:
        """
        Setup compression for rotated log files

        Args:
            handler: File handler to monitor for rotation
        """
        # Override the rotation method to compress rotated files
        original_rotate = handler.rotate if hasattr(handler, 'rotate') else None

        def compress_rotate(source: str, dest: str) -> None:
            """Rotate and compress the file"""
            # Call original rotation
            if original_rotate:
                original_rotate(source, dest)
            else:
                # Default rotation behavior
                if os.path.exists(source):
                    if os.path.exists(dest):
                        os.remove(dest)
                    os.rename(source, dest)

            # Compress the destination file
            if self.compress and dest and os.path.exists(dest):
                compressed_dest = f"{dest}.gz"
                with open(dest, 'rb') as f_in:
                    with gzip.open(compressed_dest, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(dest)

        # Patch the handler if it has a rotate method
        if hasattr(handler, 'rotate'):
            handler.rotate = compress_rotate

    def _log(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """
        Internal logging method

        Args:
            level: Log level (logging.DEBUG, INFO, etc.)
            message: Log message
            context: Context information dictionary
            metrics: Metrics dictionary
            exc_info: Include exception info if available
        """
        # Create log record with extra fields
        extra = {}
        if context:
            extra['context'] = context
        if metrics:
            extra['metrics'] = metrics

        # Log the message
        self._logger.log(level, message, extra=extra, exc_info=exc_info)

    def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, context, metrics)

    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log info message"""
        self._log(logging.INFO, message, context, metrics)

    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, context, metrics)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, context, metrics, exc_info)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, context, metrics, exc_info)

    def set_level(self, level: str) -> None:
        """
        Set logging level

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._logger.setLevel(getattr(logging, level.upper()))
        for handler in self._logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))

    def __repr__(self) -> str:
        """String representation"""
        return f"StructuredLogger(name={self.name}, format={self.format}, file={self.log_file})"
