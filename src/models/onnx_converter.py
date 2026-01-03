"""
ONNX model converter for PyTorch models.

Converts PyTorch YOLO models to ONNX format for optimized inference.
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import torch


class ONNXConversionError(Exception):
    """Raised when ONNX conversion fails."""
    pass


class ONNXConverter:
    """
    Converts PyTorch models to ONNX format.

    Features:
    - Multiple opset version support
    - Dynamic batch size
    - Model validation
    - Error handling for unsupported operators
    """

    OPTIMIZATION_LEVELS = {
        'none': [],
        'basic': ['eliminate_unused_initializer'],
        'all': [
            'eliminate_unused_initializer',
            'fuse_add_bias_into_conv',
            'fuse_bn_into_conv',
            'fuse_consecutive_concats',
            'fuse_consecutive_reduce_unsqueeze',
            'fuse_consecutive_squeezes',
            'fuse_consecutive_transposes',
            'fuse_matmul_add_bias_into_gemm',
            'fuse_pad_into_conv',
            'fuse_transpose_into_gemm',
            'eliminate_nop_transpose',
            'eliminate_nop_pad',
            'eliminate_identity',
            'eliminate_deadend'
        ]
    }

    def __init__(
        self,
        output_dir: Optional[str] = None,
        opset_version: int = 17
    ):
        """
        Initialize ONNX converter.

        Args:
            output_dir: Directory to save ONNX models (default: ~/.cache/edge-detection/models/onnx/)
            opset_version: ONNX opset version (default: 17)
        """
        if output_dir is None:
            cache_dir = Path.home() / '.cache' / 'edge-detection' / 'models' / 'onnx'
        else:
            cache_dir = Path(output_dir)

        self.output_dir = cache_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.opset_version = opset_version

    def convert(
        self,
        model_path: str,
        model_name: str,
        dynamic_batch: bool = False,
        input_size: tuple = (1, 3, 640, 640),
        optimize: bool = True
    ) -> Path:
        """
        Convert PyTorch model to ONNX format.

        Args:
            model_path: Path to PyTorch model (.pt file)
            model_name: Name for the output model
            dynamic_batch: Enable dynamic batch size
            input_size: Input tensor size (batch, channels, height, width)
            optimize: Apply graph optimization

        Returns:
            Path to converted ONNX model

        Raises:
            ONNXConversionError: If conversion fails
        """
        try:
            # Load PyTorch model
            print(f"🔧 Loading PyTorch model from {model_path}")
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = torch.load(model_path, map_location=device)

            # Set model to evaluation mode
            model.eval()

            # Create dummy input
            dummy_input = torch.randn(input_size).to(device)

            # Prepare dynamic axes if requested
            dynamic_axes = None
            if dynamic_batch:
                dynamic_axes = {
                    'images': {0: 'batch'},
                    'output': {0: 'batch'}
                }

            # Output path
            output_path = self.output_dir / f"{model_name}.onnx"

            # Convert to ONNX
            print(f"🔄 Converting to ONNX (opset {self.opset_version})...")
            start_time = time.time()

            with torch.no_grad():
                torch.onnx.export(
                    model,
                    dummy_input,
                    str(output_path),
                    opset_version=self.opset_version,
                    dynamic_axes=dynamic_axes,
                    input_names=['images'],
                    output_names=['output'],
                    export_params=True,
                    do_constant_folding=optimize,
                    verbose=False
                )

            conversion_time = time.time() - start_time
            print(f"✅ Conversion completed in {conversion_time:.2f}s")

            # Validate the model
            print("🔍 Validating ONNX model...")
            self.validate_model(str(output_path))

            # Get model size
            size_mb = self.get_model_size(str(output_path))
            print(f"📦 Model size: {size_mb:.2f} MB")

            return output_path

        except Exception as e:
            # Provide helpful error messages for common issues
            error_msg = str(e)

            if 'unsupported' in error_msg.lower() or 'not supported' in error_msg.lower():
                raise ONNXConversionError(
                    f"❌ ONNX conversion failed: Unsupported operator\n"
                    f"   Error: {error_msg}\n\n"
                    f"💡 Possible solutions:\n"
                    f"   1. Try a newer opset version: --opset {self.opset_version + 1}\n"
                    f"   2. Check if operator has ONNX equivalent\n"
                    f"   3. Consider implementing custom ONNX operator\n"
                    f"   4. Use a different model version"
                )
            elif 'shape' in error_msg.lower() or 'dimension' in error_msg.lower():
                raise ONNXConversionError(
                    f"❌ ONNX conversion failed: Shape mismatch\n"
                    f"   Error: {error_msg}\n\n"
                    f"💡 Possible solutions:\n"
                    f"   1. Check input size matches model expectations\n"
                    f"   2. Verify model architecture\n"
                    f"   3. Try with fixed batch size first"
                )
            else:
                raise ONNXConversionError(
                    f"❌ ONNX conversion failed\n"
                    f"   Error: {error_msg}\n\n"
                    f"💡 Hint: See documentation for troubleshooting"
                )

    def validate_model(self, model_path: str) -> bool:
        """
        Validate ONNX model structure.

        Args:
            model_path: Path to ONNX model

        Returns:
            True if valid, False otherwise
        """
        try:
            import onnx
            from onnx import checker

            # Load model
            model = onnx.load(model_path)

            # Check model
            checker.check_model(model)

            print("✅ ONNX model is valid")
            return True

        except Exception as e:
            print(f"❌ ONNX model validation failed: {e}")
            return False

    def get_model_size(self, model_path: str) -> float:
        """
        Get model file size in MB.

        Args:
            model_path: Path to model file

        Returns:
            Size in megabytes
        """
        path = Path(model_path)
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return size_mb

    def get_optimization_levels(self) -> Dict[str, list]:
        """
        Get available optimization levels.

        Returns:
            Dictionary of optimization levels and their passes
        """
        return self.OPTIMIZATION_LEVELS.copy()

    def get_supported_opset_versions(self) -> list:
        """
        Get list of supported ONNX opset versions.

        Returns:
            List of supported opset versions
        """
        # Commonly supported opset versions
        return [11, 12, 13, 14, 15, 16, 17, 18]

    def recommend_opset_version(self) -> int:
        """
        Recommend the best opset version.

        Returns:
            Recommended opset version
        """
        # Return the latest stable version
        supported = self.get_supported_opset_versions()
        return supported[-1]  # Return latest

    def get_conversion_info(self, model_path: str) -> Dict[str, Any]:
        """
        Get information about converted model.

        Args:
            model_path: Path to ONNX model

        Returns:
            Dictionary with model information
        """
        try:
            import onnx

            model = onnx.load(model_path)

            info = {
                'opset_version': model.opset_import[0].version if model.opset_import else None,
                'producer_name': model.producer_name,
                'producer_version': model.producer_version,
                'graph_inputs': [inp.name for inp in model.graph.input],
                'graph_outputs': [out.name for out in model.graph.output],
                'num_nodes': len(model.graph.node),
                'file_size_mb': self.get_model_size(model_path)
            }

            return info

        except Exception as e:
            return {'error': str(e)}
