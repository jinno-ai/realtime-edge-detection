"""
Context management for structured logging
Provides thread-safe context storage and retrieval
"""
import threading
from typing import Dict, Any, Optional
import copy


class ContextManager:
    """
    Thread-safe context manager for log entries

    Manages contextual information that should be included in log entries,
    such as request IDs, device information, model details, etc.

    Thread-safe for use in multi-threaded environments.
    """

    def __init__(self):
        """Initialize context manager with empty context"""
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def update(self, key: str, value: Any) -> None:
        """
        Update a context key with a value

        Args:
            key: Context key (e.g., 'request_id', 'device')
            value: Context value (can be any type, including nested dicts)
        """
        with self._lock:
            self._context[key] = copy.deepcopy(value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a context value by key

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default
        """
        with self._lock:
            return copy.deepcopy(self._context.get(key, default))

    def get_context(self) -> Dict[str, Any]:
        """
        Get a copy of the entire context dictionary

        Returns:
            Deep copy of context dictionary
        """
        with self._lock:
            return copy.deepcopy(self._context)

    def remove(self, key: str) -> None:
        """
        Remove a context key

        Args:
            key: Context key to remove
        """
        with self._lock:
            if key in self._context:
                del self._context[key]

    def clear(self) -> None:
        """Clear all context"""
        with self._lock:
            self._context.clear()

    def update_batch(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple context keys at once

        Args:
            updates: Dictionary of key-value pairs to update
        """
        with self._lock:
            for key, value in updates.items():
                self._context[key] = copy.deepcopy(value)

    def __repr__(self) -> str:
        """String representation of context"""
        with self._lock:
            return f"ContextManager({self._context})"
