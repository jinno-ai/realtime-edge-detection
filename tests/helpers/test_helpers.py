"""
Helper functions for edge detection tests

Provides utilities for assertions, mocking, and test data validation
"""

import os
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from contextlib import contextmanager


class AssertionHelpers:
    """
    Custom assertion helpers for testing
    """

    @staticmethod
    def assert_valid_bbox(bbox: List[float], image_width: int = 1920, image_height: int = 1080):
        """
        Assert that bounding box has valid coordinates

        Args:
            bbox: Bounding box [x1, y1, x2, y2]
            image_width: Image width for boundary checking
            image_height: Image height for boundary checking

        Raises:
            AssertionError: If bbox is invalid
        """
        assert isinstance(bbox, list), "Bbox must be a list"
        assert len(bbox) == 4, f"Bbox must have 4 values, got {len(bbox)}"
        assert all(isinstance(v, (int, float)) for v in bbox), "All bbox values must be numeric"

        x1, y1, x2, y2 = bbox

        assert x1 < x2, f"x1 ({x1}) must be less than x2 ({x2})"
        assert y1 < y2, f"y1 ({y1}) must be less than y2 ({y2})"
        assert x1 >= 0, f"x1 ({x1}) must be non-negative"
        assert y1 >= 0, f"y1 ({y1}) must be non-negative"
        assert x2 <= image_width, f"x2 ({x2}) must be <= image width ({image_width})"
        assert y2 <= image_height, f"y2 ({y2}) must be <= image height ({image_height})"

    @staticmethod
    def assert_valid_confidence(confidence: float):
        """
        Assert that confidence score is valid

        Args:
            confidence: Confidence score

        Raises:
            AssertionError: If confidence is invalid
        """
        assert isinstance(confidence, (int, float)), "Confidence must be numeric"
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} must be in [0.0, 1.0]"

    @staticmethod
    def assert_valid_detection(detection: Dict[str, Any],
                              image_width: int = 1920,
                              image_height: int = 1080):
        """
        Assert that detection has valid structure and values

        Args:
            detection: Detection dictionary
            image_width: Image width for bbox validation
            image_height: Image height for bbox validation

        Raises:
            AssertionError: If detection is invalid
        """
        assert isinstance(detection, dict), "Detection must be a dictionary"

        required_keys = ['bbox', 'confidence', 'class_id', 'class_name']
        for key in required_keys:
            assert key in detection, f"Detection missing required key: {key}"

        AssertionHelpers.assert_valid_bbox(detection['bbox'], image_width, image_height)
        AssertionHelpers.assert_valid_confidence(detection['confidence'])

        assert isinstance(detection['class_id'], int), "class_id must be an integer"
        assert detection['class_id'] >= 0, "class_id must be non-negative"
        assert isinstance(detection['class_name'], str), "class_name must be a string"

    @staticmethod
    def assert_detections_sorted_by_confidence(detections: List[Dict[str, Any]],
                                               descending: bool = True):
        """
        Assert that detections are sorted by confidence

        Args:
            detections: List of detections
            descending: If True, check descending order; else ascending

        Raises:
            AssertionError: If not sorted correctly
        """
        if len(detections) < 2:
            return  # Single or empty list is trivially sorted

        confidences = [d['confidence'] for d in detections]

        if descending:
            assert confidences == sorted(confidences, reverse=True), \
                "Detections not sorted by confidence (descending)"
        else:
            assert confidences == sorted(confidences), \
                "Detections not sorted by confidence (ascending)"


class TimingHelpers:
    """
    Helpers for timing and performance assertions
    """

    @staticmethod
    @contextmanager
    def assert_execution_time(max_seconds: float,
                             operation_name: str = "operation"):
        """
        Context manager to assert operation completes within time limit

        Args:
            max_seconds: Maximum allowed execution time
            operation_name: Name of operation for error message

        Example:
            with TimingHelpers.assert_execution_time(0.5, "config loading"):
                config = ConfigManager().load_config()
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            if elapsed > max_seconds:
                raise AssertionError(
                    f"{operation_name} took {elapsed:.3f}s, "
                    f"exceeding maximum of {max_seconds:.3f}s"
                )

    @staticmethod
    def measure_time(operation: Callable) -> tuple[Any, float]:
        """
        Measure execution time of an operation

        Args:
            operation: Function to measure

        Returns:
            Tuple of (result, elapsed_time_seconds)
        """
        start_time = time.time()
        result = operation()
        elapsed = time.time() - start_time
        return result, elapsed


class MockHelpers:
    """
    Helpers for creating mocks in tests
    """

    @staticmethod
    def create_video_capture_mock(fps: int = 30,
                                 frame_count: int = 300,
                                 width: int = 640,
                                 height: int = 480) -> 'Mock':
        """
        Create a mock cv2.VideoCapture object

        Args:
            fps: Frames per second
            frame_count: Number of frames to return
            width: Frame width
            height: Frame height

        Returns:
            Mock VideoCapture object
        """
        from unittest.mock import Mock, MagicMock
        import numpy as np

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: fps,      # CAP_PROP_FPS
            3: width,    # CAP_PROP_FRAME_WIDTH
            4: height    # CAP_PROP_FRAME_HEIGHT
        }.get(prop, 0)

        # Generate frames
        frames_read = 0

        def read_frame():
            nonlocal frames_read
            if frames_read < frame_count:
                frames_read += 1
                frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
                return True, frame
            else:
                return False, None

        mock_cap.read.side_effect = read_frame

        return mock_cap

    @staticmethod
    @contextmanager
    def isolated_environment(environment_prefix: str = 'EDGE_DETECTION_'):
        """
        Context manager to isolate environment variables

        Clears all environment variables with given prefix before test,
        restores them after.

        Args:
            environment_prefix: Prefix of env vars to isolate

        Example:
            with MockHelpers.isolated_environment():
                os.environ['EDGE_DETECTION_MODEL_PATH'] = 'test.pt'
                # Test code here
            # Environment restored after
        """
        # Save original env vars
        original_env = os.environ.copy()

        # Clear specified env vars
        keys_to_remove = [k for k in os.environ if k.startswith(environment_prefix)]
        for key in keys_to_remove:
            del os.environ[key]

        try:
            yield
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


class ValidationHelpers:
    """
    Helpers for validation testing
    """

    @staticmethod
    def get_validation_errors_by_param(errors: List[str],
                                       param_name: str) -> List[str]:
        """
        Filter validation errors by parameter name

        Args:
            errors: List of validation error messages
            param_name: Parameter name to filter by (e.g., 'confidence_threshold')

        Returns:
            List of error messages for the specified parameter
        """
        return [e for e in errors if param_name in e]

    @staticmethod
    def count_validation_errors(errors: List[str]) -> Dict[str, int]:
        """
        Count validation errors by parameter

        Args:
            errors: List of validation error messages

        Returns:
            Dictionary mapping parameter names to error counts
        """
        from collections import Counter

        # Extract parameter names from error messages
        # Error format: "❌ detection.confidence_threshold = 1.5"
        params = []
        for error in errors:
            if ' = ' in error:
                # Extract parameter name before " = "
                parts = error.split(' = ')[0]
                # Get last part after last space (the parameter path)
                param = parts.split()[-1]
                params.append(param)

        return dict(Counter(params))

    @staticmethod
    def assert_all_errors_have_hints(errors: List[str]):
        """
        Assert that all validation errors include hints

        Args:
            errors: List of validation error messages

        Raises:
            AssertionError: If any error is missing a hint
        """
        for error in errors:
            assert '💡' in error, f"Error missing hint: {error}"


class FileSystemHelpers:
    """
    Helpers for file system operations in tests
    """

    @staticmethod
    @contextmanager
    def temporary_directory(change_to: bool = False):
        """
        Context manager for temporary directory

        Args:
            change_to: If True, change working directory to temp dir

        Example:
            with FileSystemHelpers.temporary_directory() as temp_dir:
                # Use temp_dir
                pass
            # Directory cleaned up
        """
        import tempfile
        import shutil

        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            if change_to:
                os.chdir(temp_dir)
            yield Path(temp_dir)
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def create_file_with_content(file_path: Path, content: str):
        """
        Create file with content, creating parent directories if needed

        Args:
            file_path: Path to file
            content: Content to write
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)

    @staticmethod
    def count_files_in_directory(directory: Path,
                                pattern: str = '*') -> int:
        """
        Count files matching pattern in directory

        Args:
            directory: Directory to search
            pattern: Glob pattern (default: all files)

        Returns:
            Number of matching files
        """
        return len(list(directory.glob(pattern)))


class ConfigTestHelpers:
    """
    Helpers specific to configuration testing
    """

    @staticmethod
    def get_all_config_paths() -> List[str]:
        """
        Get all standard configuration file paths

        Returns:
            List of config file paths in search order
        """
        cwd = Path.cwd()
        home = Path.home()

        paths = [
            str(cwd / 'config.yaml'),
            str(cwd / 'config' / 'default.yaml'),
            str(home / '.config' / 'edge-detection' / 'config.yaml')
        ]

        return paths

    @staticmethod
    def get_profile_paths(profile_name: str) -> List[str]:
        """
        Get all possible paths for a profile file

        Args:
            profile_name: Name of profile

        Returns:
            List of potential profile file paths
        """
        cwd = Path.cwd()
        home = Path.home()

        paths = [
            str(cwd / 'config' / f'{profile_name}.yaml'),
            str(home / '.config' / 'edge-detection' / f'{profile_name}.yaml')
        ]

        return paths

    @staticmethod
    def clear_config_cache():
        """
        Clear any configuration caching

        Useful for tests that need to reload configuration
        """
        # Reset ConfigManager instances
        # (if any singleton pattern is implemented)
        pass


class PerformanceAssertions:
    """
    Performance-related assertions

    Covers: R-002, R-004
    """

    @staticmethod
    def assert_config_load_time(config_mgr,
                               max_ms: float = 200.0):
        """
        Assert configuration loads within time limit

        Args:
            config_mgr: ConfigManager instance
            max_ms: Maximum allowed time in milliseconds

        Raises:
            AssertionError: If loading takes too long

        Reference:
            R-004: Config loading should be < 200ms
        """
        with TimingHelpers.assert_execution_time(max_ms / 1000.0, "config loading"):
            config_mgr.load_config()

    @staticmethod
    def assert_device_detection_time(detection_func,
                                    max_ms: float = 3000.0):
        """
        Assert device detection completes within time limit

        Args:
            detection_func: Function that performs device detection
            max_ms: Maximum allowed time in milliseconds

        Raises:
            AssertionError: If detection takes too long

        Reference:
            R-002: Device detection should add < 3s to startup time
        """
        with TimingHelpers.assert_execution_time(max_ms / 1000.0, "device detection"):
            detection_func()
