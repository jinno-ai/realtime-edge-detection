"""
Device Manager for automatic hardware detection and selection.
"""

import logging
from pathlib import Path
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Supported device types."""
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon GPU
    TFLITE = "tflite"
    ONNX = "onnx"


class DeviceError(Exception):
    """Raised when device operation fails."""
    pass


class DeviceManager:
    """
    Manages device detection and selection for optimal performance.

    Implements automatic hardware detection with fallback hierarchy.
    """

    def __init__(self):
        self._available_devices = None
        self._selected_device = None
        logger.debug("DeviceManager initialized")

    def detect_devices(self) -> List[DeviceType]:
        """
        Detect available hardware devices.

        Returns:
            List of available DeviceType in priority order
        """
        if self._available_devices is not None:
            return self._available_devices

        self._available_devices = []

        # Check CUDA (NVIDIA GPU)
        if self._check_cuda():
            self._available_devices.append(DeviceType.CUDA)
            logger.info("CUDA device detected (NVIDIA GPU)")

        # Check MPS (Apple Silicon GPU)
        if self._check_mps():
            self._available_devices.append(DeviceType.MPS)
            logger.info("MPS device detected (Apple Silicon)")

        # Check TFLite
        if self._check_tflite():
            self._available_devices.append(DeviceType.TFLITE)
            logger.info("TFLite device detected")

        # CPU is always available
        self._available_devices.append(DeviceType.CPU)
        logger.info("CPU device available (fallback)")

        return self._available_devices

    def get_device(self, device_spec: str = "auto") -> DeviceType:
        """
        Get device, auto-detecting if specified.

        Args:
            device_spec: Device specification (e.g., "auto", "cpu", "cuda", "cuda:0")

        Returns:
            Selected DeviceType

        Raises:
            DeviceError: If specified device is not available
        """
        # Parse device spec (handle "cuda:0" format)
        device_base = device_spec.split(":")[0] if ":" in device_spec else device_spec

        try:
            device_type = DeviceType(device_base.lower())
        except ValueError:
            raise DeviceError(
                f"Invalid device specification: {device_spec}. "
                f"Valid options: auto, cpu, cuda, mps, tflite, onnx"
            )

        if device_type == DeviceType.AUTO:
            return self._auto_detect_device()

        # Validate requested device is available
        available = self.detect_devices()
        if device_type not in available:
            available_names = [d.value for d in available]
            raise DeviceError(
                f"Requested device '{device_type.value}' is not available. "
                f"Available devices: {', '.join(available_names)}"
            )

        self._selected_device = device_type
        logger.info(f"Using device: {device_type.value} (specified)")
        return device_type

    def _auto_detect_device(self) -> DeviceType:
        """
        Auto-detect best available device.

        Returns:
            Best available DeviceType

        Strategy:
            1. CUDA (NVIDIA GPU) - Best for inference
            2. MPS (Apple Silicon) - Good performance on Mac
            3. TFLite - Good for edge devices
            4. CPU - Always available fallback
        """
        available = self.detect_devices()

        # Select first (best) available device
        selected = available[0]
        self._selected_device = selected

        device_names = {
            DeviceType.CUDA: "cuda (NVIDIA GPU)",
            DeviceType.MPS: "mps (Apple Silicon)",
            DeviceType.TFLITE: "tflite (Edge TPU)",
            DeviceType.CPU: "cpu"
        }

        logger.info(f"Auto-detected device: {device_names.get(selected, selected.value)}")
        return selected

    def _check_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            available = torch.cuda.is_available()
            if available:
                device_count = torch.cuda.device_count()
                logger.debug(f"Found {device_count} CUDA device(s)")
            return available
        except ImportError:
            logger.debug("PyTorch not available, cannot check CUDA")
            return False
        except Exception as e:
            logger.warning(f"Error checking CUDA: {e}")
            return False

    def _check_mps(self) -> bool:
        """Check if MPS (Apple Silicon) is available."""
        try:
            import torch
            available = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
            if available:
                logger.debug("MPS (Apple Silicon) is available")
            return available
        except ImportError:
            logger.debug("PyTorch not available, cannot check MPS")
            return False
        except Exception as e:
            logger.warning(f"Error checking MPS: {e}")
            return False

    def _check_tflite(self) -> bool:
        """Check if TFLite is available."""
        try:
            import tflite_runtime
            logger.debug("TFLite runtime is available")
            return True
        except ImportError:
            logger.debug("TFLite runtime not available")
            return False
        except Exception as e:
            logger.warning(f"Error checking TFLite: {e}")
            return False

    def get_device_info(self, device_type: DeviceType) -> dict:
        """
        Get detailed information about a device.

        Args:
            device_type: Device type to query

        Returns:
            Dictionary with device information
        """
        info = {
            "type": device_type.value,
            "available": device_type in self.detect_devices()
        }

        if device_type == DeviceType.CUDA:
            try:
                import torch
                if torch.cuda.is_available():
                    info["device_count"] = torch.cuda.device_count()
                    info["current_device"] = torch.cuda.current_device()
                    info["device_name"] = torch.cuda.get_device_name(0)
            except Exception as e:
                logger.warning(f"Error getting CUDA info: {e}")

        elif device_type == DeviceType.MPS:
            try:
                import torch
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    info["available"] = True
                    info["backend"] = "MPS (Apple Silicon)"
            except Exception as e:
                logger.warning(f"Error getting MPS info: {e}")

        return info

    def list_available_devices(self) -> str:
        """
        Get human-readable list of available devices.

        Returns:
            Formatted string listing available devices
        """
        available = self.detect_devices()
        lines = ["Available devices:"]

        for device in available:
            info = self.get_device_info(device)
            device_desc = f"  - {info['type']}"
            if 'device_name' in info:
                device_desc += f": {info['device_name']}"
            if 'device_count' in info:
                device_desc += f" ({info['device_count']} device(s))"
            lines.append(device_desc)

        return "\n".join(lines)

    def get_torch_device(self, device_type: Optional[DeviceType] = None) -> 'torch.device':
        """
        Get PyTorch device object.

        Args:
            device_type: Device type (uses selected if None)

        Returns:
            torch.device object

        Raises:
            ImportError: If PyTorch is not available
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is required for device selection")

        if device_type is None:
            device_type = self._selected_device or self.get_device()

        if device_type == DeviceType.CUDA:
            return torch.device("cuda")
        elif device_type == DeviceType.MPS:
            return torch.device("mps")
        else:
            return torch.device("cpu")
