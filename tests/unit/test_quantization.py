"""
Unit tests for quantization pipeline.
"""

import pytest
import torch
import torch.nn as nn
from pathlib import Path
import tempfile

from src.models.quantization import (
    QuantizationPipeline,
    QuantizationFormat,
    QuantizationBackend,
    QUANTIZATION_CONFIGS
)
from src.models.calibrator import Calibrator
from src.models.accuracy_validator import AccuracyValidator


class MockModel(nn.Module):
    """Mock model for testing."""
    
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3)
        self.conv2 = nn.Conv2d(16, 32, 3)
        self.fc = nn.Linear(32 * 636 * 636, 80)  # Simplified
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


class TestQuantizationConfigs:
    """Test quantization configuration."""
    
    def test_supported_formats(self):
        """Test that INT8 and FP16 formats are defined."""
        assert 'int8' in QUANTIZATION_CONFIGS
        assert 'fp16' in QUANTIZATION_CONFIGS
    
    def test_int8_config(self):
        """Test INT8 configuration values."""
        config = QUANTIZATION_CONFIGS['int8']
        assert config['size_reduction'] == 0.75
        assert config['accuracy_loss_threshold'] == 0.02
        assert 'pytorch' in config['backends']
    
    def test_fp16_config(self):
        """Test FP16 configuration values."""
        config = QUANTIZATION_CONFIGS['fp16']
        assert config['size_reduction'] == 0.50
        assert config['accuracy_loss_threshold'] == 0.005
        assert 'pytorch' in config['backends']


class TestQuantizationPipeline:
    """Test QuantizationPipeline class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.pipeline = QuantizationPipeline()
        self.model = MockModel()
    
    def test_initialization(self):
        """Test pipeline initialization."""
        assert self.pipeline.cache_dir.exists()
        assert self.pipeline.model_dir.exists()
    
    def test_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported quantization format"):
            self.pipeline.quantize(self.model, format='uint8', backend='pytorch')
    
    def test_invalid_backend_combination_raises_error(self):
        """Test that invalid backend combination raises ValueError."""
        # FP16 not supported by ONNX backend
        with pytest.raises(ValueError, match="not supported by backend"):
            self.pipeline.quantize(
                self.model,
                format='fp16',
                backend='onnx'
            )
    
    def test_pytorch_fp16_quantization(self):
        """Test PyTorch FP16 quantization."""
        quantized_model, stats = self.pipeline.quantize(
            self.model,
            format='fp16',
            backend='pytorch',
            validate_accuracy=False
        )
        
        assert quantized_model is not None
        assert stats['format'] == 'fp16'
        assert stats['backend'] == 'pytorch'
        assert stats['size_reduction'] > 0
        assert stats['quantization_time_sec'] > 0
    
    def test_pytorch_int8_quantization(self):
        """Test PyTorch INT8 quantization."""
        quantized_model, stats = self.pipeline.quantize(
            self.model,
            format='int8',
            backend='pytorch',
            calibration_data=None,  # Use dynamic quantization
            validate_accuracy=False
        )
        
        assert quantized_model is not None
        assert stats['format'] == 'int8'
        assert stats['backend'] == 'pytorch'
    
    def test_get_model_size(self):
        """Test model size calculation."""
        size = self.pipeline._get_model_size(self.model)
        assert size > 0
        assert size < 100  # Should be less than 100MB for this small model
    
    def test_save_quantized_model(self):
        """Test saving quantized model."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "quantized_model.pt"
            stats = {'format': 'int8', 'size_reduction': 0.75}
            
            self.pipeline.save_quantized_model(
                self.model,
                str(output_path),
                'int8',
                stats
            )
            
            assert output_path.exists()
            assert output_path.with_suffix('.json').exists()


class TestCalibrator:
    """Test Calibrator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Use temp directory for testing
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.calibrator = Calibrator(cache_dir=Path(self.temp_dir))
    
    def test_initialization(self):
        """Test calibrator initialization."""
        assert self.calibrator.cache_dir.exists()
    
    def test_unavailable_calibration_data(self):
        """Test handling of unavailable calibration data."""
        # Should raise error or return empty list when data not available
        # and not downloading
        with pytest.raises(Exception):
            self.calibrator._load_calibration_images(
                Path('/nonexistent/path'),
                num_images=10
            )


class TestAccuracyValidator:
    """Test AccuracyValidator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = AccuracyValidator(
            map_threshold=0.02,
            validation_images=10
        )
    
    def test_initialization(self):
        """Test validator initialization."""
        assert self.validator.map_threshold == 0.02
        assert self.validator.validation_images == 10
    
    def test_compute_map_returns_float(self):
        """Test that _compute_map returns float."""
        results = []
        map_score = self.validator._compute_map(results)
        assert isinstance(map_score, float)
        assert 0 <= map_score <= 1
    
    def test_validate_returns_dict_with_required_keys(self):
        """Test that validate returns dict with required keys."""
        model1 = MockModel()
        model2 = MockModel()
        validation_data = []
        
        results = self.validator.validate(
            model1,
            model2,
            validation_data
        )
        
        assert 'fp32_map' in results
        assert 'quantized_map' in results
        assert 'degradation' in results
        assert 'threshold' in results
        assert 'passes' in results


class TestQuantizationFormat:
    """Test QuantizationFormat enum."""
    
    def test_int8_format(self):
        """Test INT8 format enum."""
        assert QuantizationFormat.INT8.value == 'int8'
    
    def test_fp16_format(self):
        """Test FP16 format enum."""
        assert QuantizationFormat.FP16.value == 'fp16'


class TestQuantizationBackend:
    """Test QuantizationBackend enum."""
    
    def test_pytorch_backend(self):
        """Test PyTorch backend enum."""
        assert QuantizationBackend.PYTORCH.value == 'pytorch'
    
    def test_tensorrt_backend(self):
        """Test TensorRT backend enum."""
        assert QuantizationBackend.TENSORRT.value == 'tensorrt'
    
    def test_onnx_backend(self):
        """Test ONNX backend enum."""
        assert QuantizationBackend.ONNX.value == 'onnx'


class TestIntegration:
    """Integration tests for quantization workflow."""
    
    def test_full_quantization_workflow(self):
        """Test complete quantization workflow."""
        pipeline = QuantizationPipeline()
        model = MockModel()
        
        # Quantize
        quantized_model, stats = pipeline.quantize(
            model,
            format='fp16',
            backend='pytorch',
            validate_accuracy=False
        )
        
        # Save
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "model.fp16.pt"
            pipeline.save_quantized_model(
                quantized_model,
                str(output_path),
                'fp16',
                stats
            )
            
            # Verify files exist
            assert output_path.exists()
            assert output_path.with_suffix('.json').exists()
            
            # Load and verify stats
            import json
            with open(output_path.with_suffix('.json')) as f:
                saved_stats = json.load(f)
            
            assert saved_stats['format'] == 'fp16'
            assert saved_stats['size_reduction'] > 0
