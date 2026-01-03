"""Device management for edge detection inference."""

from typing import Optional, Dict, Any
import torch

from src.hardware.device_detector import DeviceDetector, DeviceType


class DeviceManager:
    """
    Manages device selection and provides device handles.

    AC Reference: #1-5
    """

    def __init__(self, device_str: str = "auto"):
        """
        Initialize DeviceManager.

        Args:
            device_str: Device specification ("auto", "cpu", "cuda", "cuda:0", "mps", "tpu")

        AC Reference: #2
        """
        self._detector = DeviceDetector()
        self.gpu_id: Optional[int] = None

        # Extract GPU ID if present
        if device_str.startswith("cuda:"):
            self.gpu_id = int(device_str.split(":")[1])
        elif device_str == "cuda":
            # Default to first GPU if just "cuda" specified
            self.gpu_id = 0

        self.selected_device: DeviceType = self.parse_device_string(device_str)

    def parse_device_string(self, device_str: str) -> DeviceType:
        """
        Parse device string and return DeviceType.

        Args:
            device_str: Device specification

        Returns:
            Parsed DeviceType

        Raises:
            ValueError: If device string is invalid

        AC Reference: #2, #5
        """
        if device_str == "auto":
            return self._auto_detect()

        if device_str == "cpu":
            return DeviceType.CPU

        if device_str == "cuda":
            return DeviceType.CUDA

        if device_str.startswith("cuda:"):
            # Handle cuda:0, cuda:1, etc.
            parts = device_str.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid device format: {device_str}")

            try:
                gpu_id = int(parts[1])
                if gpu_id < 0:
                    raise ValueError(f"GPU ID must be non-negative: {gpu_id}")
            except ValueError as e:
                raise ValueError(f"Invalid GPU ID: {parts[1]}") from e

            return DeviceType.CUDA

        if device_str == "mps":
            return DeviceType.MPS

        if device_str == "tpu":
            return DeviceType.TFLITE

        raise ValueError(f"Unknown device: {device_str}")

    def _auto_detect(self) -> DeviceType:
        """
        Run auto device detection.

        Returns:
            Detected device type

        AC Reference: #1
        """
        return self._detector.detect_device()

    def validate_device(self) -> None:
        """
        Validate that selected device is available.

        Raises:
            RuntimeError: If selected device is not available

        AC Reference: #3
        """
        if self.selected_device == DeviceType.CUDA:
            if not torch.cuda.is_available():
                available = self._detector.list_available_devices()
                devices_list = []
                for dev_name, dev_info in available.items():
                    if dev_info["available"]:
                        if dev_name == "cuda" and "gpus" in dev_info:
                            devices_list.append(
                                f"   - {dev_name} ({dev_info['gpus'][0]['name']})"
                            )
                        else:
                            devices_list.append(f"   - {dev_name}")

                devices_str = "\n".join(devices_list) if devices_list else "   None"

                raise RuntimeError(
                    f"Device 'cuda' is not available on this system.\n\n"
                    f"Available devices:\n"
                    f"{devices_str}\n\n"
                    f"Hint: Use --device cpu to run on CPU"
                )

            # Validate specific GPU ID if set
            if self.gpu_id is not None:
                device_count = torch.cuda.device_count()
                if self.gpu_id >= device_count:
                    raise RuntimeError(
                        f"GPU ID {self.gpu_id} not available. "
                        f"Available GPUs: {device_count}"
                    )

        elif self.selected_device == DeviceType.MPS:
            if not torch.backends.mps.is_available():
                raise RuntimeError("Device 'mps' is not available on this system")

    def get_torch_device(self) -> torch.device:
        """
        Get torch.device object for current device.

        Returns:
            torch.device object

        AC Reference: #1-5
        """
        if self.selected_device == DeviceType.CPU:
            return torch.device("cpu")

        elif self.selected_device == DeviceType.CUDA:
            if self.gpu_id is not None:
                return torch.device(f"cuda:{self.gpu_id}")
            return torch.device("cuda")

        elif self.selected_device == DeviceType.MPS:
            return torch.device("mps")

        else:
            # Fallback to CPU for unsupported devices
            return torch.device("cpu")

    @property
    def device_string(self) -> str:
        """
        Get string representation of current device.

        Returns:
            Device string (e.g., "cpu", "cuda:0", "mps")
        """
        if self.selected_device == DeviceType.CUDA and self.gpu_id is not None:
            return f"cuda:{self.gpu_id}"
        return self.selected_device.value

    def get_device_info(self) -> Dict[str, Any]:
        """
        Get information about current device.

        Returns:
            Dictionary with device information

        AC Reference: #1, #5
        """
        info = {
            "device_type": self.selected_device.value,
            "device_string": self.device_string,
        }

        if self.selected_device == DeviceType.CUDA and torch.cuda.is_available():
            gpu_id = self.gpu_id if self.gpu_id is not None else 0
            gpu_info = self._detector.get_gpu_info(gpu_id)
            info.update(gpu_info)
            info["gpu_count"] = self._detector.get_gpu_count()

        return info

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "DeviceManager":
        """
        Create DeviceManager from configuration dictionary.

        Args:
            config: Configuration dictionary with 'device' key

        Returns:
            DeviceManager instance

        AC Reference: #4
        """
        device_str = config.get("device", "auto")
        return cls(device_str=device_str)
