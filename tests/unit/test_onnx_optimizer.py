"""
Tests for ONNX optimizer.
"""

import pytest
from pathlib import Path
import tempfile
from src.models.onnx_optimizer import ONNXOptimizer


class TestONNXOptimizer:
    """Test suite for ONNXOptimizer class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_onnx_model(self, temp_dir):
        """Create a sample ONNX model file."""
        model_path = temp_dir / "model.onnx"
        import onnx
        from onnx import helper, TensorProto
        import numpy as np
        weight = np.random.rand(3, 3).astype(np.float32)
        init = helper.make_tensor('w', TensorProto.FLOAT, weight.shape, weight)
        node = helper.make_node('Identity', ['x'], ['y'])
        graph = helper.make_graph(
            [node], 'g',
            [helper.make_tensor_value_info('x', TensorProto.FLOAT, [1, 3])],
            [helper.make_tensor_value_info('y', TensorProto.FLOAT, [1, 3])],
            initializer=[init])  # unused initializer: gives passes work to do
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 13)])
        model.ir_version = 10
        onnx.save(model, str(model_path))
        return model_path

    def test_optimizer_initialization(self):
        """Test ONNXOptimizer initialization."""
        optimizer = ONNXOptimizer()
        assert optimizer is not None

    def test_optimize_graph_basic(self, sample_onnx_model, temp_dir):
        """Test basic graph optimization."""
        optimizer = ONNXOptimizer()

        output_path = optimizer.optimize(
            model_path=str(sample_onnx_model),
            output_path=str(temp_dir / "optimized.onnx"),
            level='basic'
        )

        assert Path(output_path).exists()

    def test_optimize_all_passes(self, sample_onnx_model, temp_dir):
        """Test optimization with all passes enabled."""
        optimizer = ONNXOptimizer()

        output_path = optimizer.optimize(
            model_path=str(sample_onnx_model),
            output_path=str(temp_dir / "optimized_all.onnx"),
            level='all'
        )

        assert Path(output_path).exists()

    def test_constant_folding(self, sample_onnx_model):
        """Test constant folding optimization."""
        optimizer = ONNXOptimizer()

        optimized = optimizer.apply_constant_folding(str(sample_onnx_model))
        assert optimized is not None

    def test_remove_redundant_nodes(self, sample_onnx_model):
        """Test removing redundant nodes."""
        optimizer = ONNXOptimizer()

        optimized = optimizer.remove_redundant_nodes(str(sample_onnx_model))
        assert optimized is not None

    def test_get_size_reduction(self, sample_onnx_model, temp_dir):
        """Test calculating size reduction after optimization."""
        optimizer = ONNXOptimizer()

        # Create optimized version
        optimized_path = str(temp_dir / "optimized.onnx")
        original_bytes = sample_onnx_model.read_bytes()
        Path(optimized_path).write_bytes(original_bytes[:len(original_bytes) // 2])  # Smaller than original

        reduction = optimizer.get_size_reduction(
            original=str(sample_onnx_model),
            optimized=optimized_path
        )

        assert reduction > 0  # Should show reduction

    def test_optimization_levels(self):
        """Test that different optimization levels are available."""
        optimizer = ONNXOptimizer()

        levels = optimizer.get_optimization_levels()
        assert 'none' in levels
        assert 'basic' in levels
        assert 'all' in levels
