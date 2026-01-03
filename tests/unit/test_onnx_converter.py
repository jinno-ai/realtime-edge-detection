"""
Tests for ONNX model converter.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from src.models.onnx_converter import ONNXConverter, ONNXConversionError


class TestONNXConverter:
    """Test suite for ONNXConverter class."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_pytorch_model_path(self, tmp_path):
        """Create a sample PyTorch model file for testing."""
        # This would normally be a real .pt file
        # For testing, we'll mock the model loading
        model_path = tmp_path / "test_model.pt"
        model_path.touch()
        return model_path

    def test_converter_initialization(self, temp_output_dir):
        """Test ONNXConverter can be initialized."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )
        assert converter.output_dir == temp_output_dir
        assert converter.opset_version == 17

    def test_convert_model_basic(self, sample_pytorch_model_path, temp_output_dir):
        """Test basic PyTorch to ONNX conversion."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )

        # This test will fail until we implement the converter
        output_path = converter.convert(
            model_path=str(sample_pytorch_model_path),
            model_name="test_model"
        )

        assert output_path.exists()
        assert output_path.suffix == ".onnx"

    def test_convert_with_dynamic_batch(self, sample_pytorch_model_path, temp_output_dir):
        """Test ONNX conversion with dynamic batch size."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )

        output_path = converter.convert(
            model_path=str(sample_pytorch_model_path),
            model_name="test_model_dynamic",
            dynamic_batch=True
        )

        assert output_path.exists()

    def test_convert_with_different_opset(self, sample_pytorch_model_path, temp_output_dir):
        """Test conversion with different opset versions."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=14
        )

        output_path = converter.convert(
            model_path=str(sample_pytorch_model_path),
            model_name="test_model_opset14"
        )

        assert output_path.exists()

    def test_unsupported_operator_error(self, temp_output_dir):
        """Test error handling for unsupported operators."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )

        # Test with a model that has unsupported ops
        # This should raise ONNXConversionError with helpful message
        with pytest.raises(ONNXConversionError) as exc_info:
            converter.convert(
                model_path="nonexistent_model.pt",
                model_name="test"
            )

        assert "conversion failed" in str(exc_info.value).lower()

    def test_validate_onnx_model(self, temp_output_dir):
        """Test ONNX model validation."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )

        # Create a dummy ONNX file for validation testing
        onnx_file = temp_output_dir / "test.onnx"
        onnx_file.write_text("dummy content")

        # This should validate the model structure
        is_valid = converter.validate_model(str(onnx_file))
        # Will fail until validation is implemented
        assert isinstance(is_valid, bool)

    def test_get_model_size(self, temp_output_dir):
        """Test getting ONNX model file size."""
        converter = ONNXConverter(
            output_dir=str(temp_output_dir),
            opset_version=17
        )

        # Create test file
        onnx_file = temp_output_dir / "test.onnx"
        onnx_file.write_bytes(b"x" * 1024)  # 1KB file

        size_mb = converter.get_model_size(str(onnx_file))
        assert size_mb == 1024 / (1024 * 1024)  # ~0.001 MB
