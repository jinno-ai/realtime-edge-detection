"""
Quantize command for edge detection CLI.

Provides CLI interface for model quantization.
"""

import argparse
import sys
from pathlib import Path

import torch

from src.models.quantization import QuantizationPipeline, QUANTIZATION_CONFIGS
from src.models.calibrator import Calibrator
from src.models.accuracy_validator import AccuracyValidator


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for quantize command."""
    parser = argparse.ArgumentParser(
        description='Quantize edge detection models for optimized inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # INT8 quantization with PyTorch
  python run.py quantize --model yolov8n.pt --format int8

  # FP16 quantization
  python run.py quantize --model yolov8n.pt --format fp16

  # Skip accuracy validation (faster)
  python run.py quantize --model yolov8n.pt --format int8 --skip-validation

  # Specify output path
  python run.py quantize --model yolov8n.pt --format int8 --output ./models/yolov8n.int8.pt
        '''
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to PyTorch model file (.pt)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['int8', 'fp16'],
        default='int8',
        help='Quantization format (default: int8)'
    )
    
    parser.add_argument(
        '--backend',
        type=str,
        choices=['pytorch', 'tensorrt', 'onnx'],
        default='pytorch',
        help='Quantization backend (default: pytorch)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for quantized model (default: ~/.cache/edge-detection/models/)'
    )
    
    parser.add_argument(
        '--calib-data',
        type=str,
        default=None,
        help='Path to calibration dataset for INT8 (default: auto-download)'
    )
    
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip accuracy validation (faster, but not recommended)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force quantization even if accuracy degradation exceeds threshold'
    )
    
    return parser


def quantize_command(args):
    """Execute quantize command."""
    print("=" * 60)
    print("🔧 Edge Detection Model Quantization")
    print("=" * 60)
    
    # Validate model path
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Error: Model file not found: {model_path}")
        sys.exit(1)
    
    print(f"\n📁 Model: {model_path}")
    print(f"📊 Format: {args.format.upper()}")
    print(f"🔧 Backend: {args.backend.upper()}")
    
    # Load model
    print(f"\n🧠 Loading model...")
    try:
        checkpoint = torch.load(model_path, map_location='cpu')
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            # Quantized model checkpoint
            state_dict = checkpoint['model_state_dict']
            print("   ⚠️  Model appears to be already quantized")
        else:
            # Regular model checkpoint
            state_dict = checkpoint
        
        # For YOLO models, we need to load through the model class
        # For simplicity, create a mock model
        from src.models.yolo_detector import YOLODetector
        config = {'model': {'path': str(model_path)}}
        detector = YOLODetector(config=config)
        detector.load_model()
        model = detector.model
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print(f"   Make sure {model_path} is a valid PyTorch model")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = QuantizationPipeline()
    
    # Prepare calibration data if needed
    calibration_data = None
    if args.format == 'int8' and not args.skip_validation:
        print("\n📊 Preparing calibration data...")
        calibrator = Calibrator()
        try:
            calibration_data = calibrator.get_calibration_data(num_images=100)
        except Exception as e:
            print(f"⚠️  Warning: Could not load calibration data: {e}")
            print("   Using dynamic quantization instead")
    
    # Quantize
    print("\n🔧 Starting quantization...")
    try:
        quantized_model, stats = pipeline.quantize(
            model,
            format=args.format,
            backend=args.backend,
            calibration_data=calibration_data,
            validate_accuracy=not args.skip_validation
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Quantization failed: {e}")
        sys.exit(1)
    
    # Check accuracy warning
    if stats.get('accuracy_warning', False):
        if not args.force:
            print(f"\n⚠️  Accuracy degradation exceeds threshold!")
            print(f"   Use --force to accept the loss and continue")
            sys.exit(1)
        else:
            print(f"\n⚠️  Proceeding despite accuracy degradation (--force specified)")
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        model_name = model_path.stem
        extension = f".{args.format}.pt"
        output_path = str(
            Path.home() / '.cache' / 'edge-detection' / 'models' / f"{model_name}{extension}"
        )
    
    # Save quantized model
    print(f"\n💾 Saving quantized model...")
    pipeline.save_quantized_model(quantized_model, output_path, args.format, stats)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Quantization Complete")
    print("=" * 60)
    print(f"\nModel: {model_path}")
    print(f"Output: {output_path}")
    print(f"\nSize: {stats['size_before_mb']:.1f}MB → {stats['size_after_mb']:.1f}MB")
    print(f"Reduction: {stats['size_reduction']*100:.1f}%")
    print(f"Time: {stats['quantization_time_sec']:.1f}s")
    
    if 'map_fp32' in stats:
        print(f"\nAccuracy:")
        print(f"  FP32 mAP: {stats['map_fp32']:.1%}")
        print(f"  {args.format.upper()} mAP: {stats['map_quantized']:.1%}")
        print(f"  Degradation: {stats['accuracy_degradation']*100:.2f}%")
    
    print(f"\n💡 Usage: python run.py detect --model {output_path} image.jpg")


def main():
    """Main entry point for quantize command."""
    parser = create_parser()
    args = parser.parse_args()
    quantize_command(args)


if __name__ == '__main__':
    main()
