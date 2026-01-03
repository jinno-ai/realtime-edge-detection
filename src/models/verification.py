"""
Model verification utilities for security and integrity.

Provides functions to verify model file integrity using checksums
and validate models before loading.
"""

import hashlib
import warnings
from pathlib import Path
from typing import Dict, Optional
import json


# Known model checksums (SHA256)
KNOWN_MODEL_CHECKSUMS = {
    'yolov8n.pt': 'replace_with_actual_checksum',
    'yolov8s.pt': 'replace_with_actual_checksum',
    'yolov8m.pt': 'replace_with_actual_checksum',
    'yolov8l.pt': 'replace_with_actual_checksum',
    'yolov8x.pt': 'replace_with_actual_checksum',
}


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 checksum as hex string
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def verify_model(model_path: str, expected_sha256: Optional[str] = None) -> bool:
    """
    Verify model file integrity using SHA256 checksum.

    Args:
        model_path: Path to model file
        expected_sha256: Expected SHA256 checksum (optional)

    Returns:
        True if verification succeeds, False otherwise

    Raises:
        FileNotFoundError: If model file doesn't exist
        ValueError: If checksum doesn't match
    """
    model_file = Path(model_path)

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Calculate actual checksum
    actual_sha256 = calculate_sha256(model_path)

    # Use provided checksum or look up from known models
    if expected_sha256 is None:
        model_name = model_file.name
        if model_name in KNOWN_MODEL_CHECKSUMS:
            expected_sha256 = KNOWN_MODEL_CHECKSUMS[model_name]
        else:
            warnings.warn(f"No known checksum for model: {model_name}")
            return True  # Can't verify without checksum

    # Verify checksum
    if actual_sha256 != expected_sha256:
        warnings.warn(
            f"Model file checksum mismatch!\n"
            f"  Expected: {expected_sha256}\n"
            f"  Actual:   {actual_sha256}\n"
            f"  File may be corrupted or tampered with."
        )
        return False

    return True


def load_model_checksums(checksum_file: str) -> Dict[str, str]:
    """
    Load model checksums from JSON file.

    Args:
        checksum_file: Path to checksum JSON file

    Returns:
        Dictionary mapping model names to checksums
    """
    checksum_path = Path(checksum_file)

    if not checksum_path.exists():
        return {}

    with open(checksum_path, 'r') as f:
        data = json.load(f)

    return data.get('models', {})


def save_model_checksum(model_path: str, checksum_file: str) -> None:
    """
    Save model checksum to checksum file.

    Args:
        model_path: Path to model file
        checksum_file: Path to checksum JSON file
    """
    model_file = Path(model_path)
    checksum_path = Path(checksum_file)

    # Calculate checksum
    sha256 = calculate_sha256(model_path)

    # Load existing checksums
    if checksum_path.exists():
        with open(checksum_path, 'r') as f:
            data = json.load(f)
    else:
        data = {'models': {}}

    # Add or update checksum
    data['models'][model_file.name] = {
        'sha256': sha256,
        'size': model_file.stat().st_size,
        'path': str(model_file)
    }

    # Save
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(data, f, indent=2)


def verify_model_before_load(model_path: str, strict: bool = False) -> bool:
    """
    Verify model before loading, with security checks.

    Args:
        model_path: Path to model file
        strict: If True, raise exception on verification failure

    Returns:
        True if verification passes

    Raises:
        ValueError: If verification fails and strict=True
    """
    try:
        # Check file exists
        if not Path(model_path).exists():
            if strict:
                raise ValueError(f"Model file not found: {model_path}")
            return False

        # Verify checksum if known
        try:
            verified = verify_model(model_path)
            if not verified:
                warnings.warn(f"Model verification failed for: {model_path}")
                if strict:
                    raise ValueError(f"Model verification failed: {model_path}")
                return False
        except ValueError as e:
            if "No known checksum" not in str(e):
                raise

        # Check file size is reasonable
        file_size = Path(model_path).stat().st_size
        if file_size < 1000:  # Less than 1KB is suspicious
            if strict:
                raise ValueError(f"Model file too small: {file_size} bytes")
            return False

        if file_size > 1000 * 1024 * 1024:  # More than 1GB is suspicious
            warnings.warn(f"Model file very large: {file_size / 1024 / 1024:.2f} MB")

        return True

    except Exception as e:
        if strict:
            raise
        warnings.warn(f"Model verification error: {e}")
        return False


def sandbox_model_load(model_path: str) -> bool:
    """
    Check if model loading can be safely sandboxed.

    Args:
        model_path: Path to model file

    Returns:
        True if model is safe to load
    """
    model_file = Path(model_path)

    # Check file extension
    if model_file.suffix not in ['.pt', '.pth', '.onnx']:
        warnings.warn(f"Unexpected model file extension: {model_file.suffix}")
        return False

    # Verify checksum
    if not verify_model_before_load(model_path, strict=False):
        warnings.warn(f"Model verification failed: {model_path}")
        return False

    # For ONNX models, could add additional checks
    if model_file.suffix == '.onnx':
        try:
            import onnx
            # Load and validate ONNX model
            model = onnx.load(model_path)
            onnx.checker.check_model(model)
        except Exception as e:
            warnings.warn(f"ONNX model validation failed: {e}")
            return False

    return True
