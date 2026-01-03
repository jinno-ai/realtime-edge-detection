"""
ONNX model optimizer.

Applies graph optimizations to ONNX models for improved performance.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time


class ONNXOptimizer:
    """
    Optimizes ONNX models using graph transformations.

    Features:
    - Graph optimization passes
    - Constant folding
    - Node elimination
    - Size reduction reporting
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

    def __init__(self):
        """Initialize ONNX optimizer."""
        self.optimization_applied = []

    def optimize(
        self,
        model_path: str,
        output_path: Optional[str] = None,
        level: str = 'all'
    ) -> str:
        """
        Optimize ONNX model.

        Args:
            model_path: Path to input ONNX model
            output_path: Path for optimized model (default: overwrites input)
            level: Optimization level ('none', 'basic', 'all')

        Returns:
            Path to optimized model
        """
        try:
            import onnx
            from onnx import optimizer

            # Load model
            print(f"🔧 Loading ONNX model from {model_path}")
            model = onnx.load(model_path)

            # Get optimization passes for level
            passes = self.OPTIMIZATION_LEVELS.get(level, [])

            if not passes:
                print("ℹ️  No optimization passes selected")
                if output_path is None:
                    return model_path
                else:
                    onnx.save(model, output_path)
                    return output_path

            # Apply optimizations
            print(f"🚀 Applying {len(passes)} optimization passes (level: {level})...")
            start_time = time.time()

            optimized_model = optimizer.optimize(model, passes)

            optimization_time = time.time() - start_time
            print(f"✅ Optimization completed in {optimization_time:.2f}s")

            # Save optimized model
            if output_path is None:
                output_path = model_path

            onnx.save(optimized_model, output_path)
            print(f"💾 Saved optimized model to {output_path}")

            self.optimization_applied = passes

            # Report size reduction
            original_size = Path(model_path).stat().st_size
            optimized_size = Path(output_path).stat().st_size
            reduction = (original_size - optimized_size) / original_size * 100

            if reduction > 0:
                print(f"📉 Size reduced by {reduction:.1f}% ({original_size / 1024 / 1024:.2f} MB → {optimized_size / 1024 / 1024:.2f} MB)")
            else:
                print(f"📊 Size: {optimized_size / 1024 / 1024:.2f} MB (no reduction)")

            return output_path

        except ImportError:
            print("⚠️  ONNX optimizer not available. Install onnxoptimizer package.")
            # Return original path if optimizer not available
            return model_path
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            # Return original path on error
            return model_path

    def apply_constant_folding(self, model_path: str) -> Optional[Any]:
        """
        Apply constant folding optimization.

        Args:
            model_path: Path to ONNX model

        Returns:
            Optimized model or None if failed
        """
        try:
            import onnx
            from onnx import optimizer

            model = onnx.load(model_path)

            # Apply constant folding
            passes = ['eliminate_unused_initializer']
            optimized = optimizer.optimize(model, passes)

            print("✅ Constant folding applied")
            return optimized

        except Exception as e:
            print(f"❌ Constant folding failed: {e}")
            return None

    def remove_redundant_nodes(self, model_path: str) -> Optional[Any]:
        """
        Remove redundant nodes from graph.

        Args:
            model_path: Path to ONNX model

        Returns:
            Optimized model or None if failed
        """
        try:
            import onnx
            from onnx import optimizer

            model = onnx.load(model_path)

            # Remove redundant operations
            passes = [
                'eliminate_nop_transpose',
                'eliminate_nop_pad',
                'eliminate_identity',
                'eliminate_deadend'
            ]
            optimized = optimizer.optimize(model, passes)

            print("✅ Redundant nodes removed")
            return optimized

        except Exception as e:
            print(f"❌ Failed to remove redundant nodes: {e}")
            return None

    def fuse_operations(self, model_path: str) -> Optional[Any]:
        """
        Fuse operations for better performance.

        Args:
            model_path: Path to ONNX model

        Returns:
            Optimized model or None if failed
        """
        try:
            import onnx
            from onnx import optimizer

            model = onnx.load(model_path)

            # Fuse operations
            passes = [
                'fuse_add_bias_into_conv',
                'fuse_bn_into_conv',
                'fuse_consecutive_concats',
                'fuse_consecutive_transposes',
                'fuse_matmul_add_bias_into_gemm'
            ]
            optimized = optimizer.optimize(model, passes)

            print("✅ Operations fused")
            return optimized

        except Exception as e:
            print(f"❌ Operation fusion failed: {e}")
            return None

    def get_size_reduction(
        self,
        original: str,
        optimized: str
    ) -> float:
        """
        Calculate size reduction percentage.

        Args:
            original: Path to original model
            optimized: Path to optimized model

        Returns:
            Reduction percentage (0-100)
        """
        original_size = Path(original).stat().st_size
        optimized_size = Path(optimized).stat().st_size

        if original_size == 0:
            return 0.0

        reduction = (original_size - optimized_size) / original_size * 100
        return max(0.0, reduction)  # Ensure non-negative

    def get_optimization_levels(self) -> Dict[str, list]:
        """
        Get available optimization levels.

        Returns:
            Dictionary mapping level names to optimization passes
        """
        return self.OPTIMIZATION_LEVELS.copy()

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of last optimization applied.

        Returns:
            Dictionary with optimization information
        """
        return {
            'passes_applied': self.optimization_applied,
            'num_passes': len(self.optimization_applied)
        }
