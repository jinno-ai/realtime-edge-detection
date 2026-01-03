"""
Export command for model conversion.

Exports PyTorch models to ONNX format.
"""

import argparse
import sys
from pathlib import Path
from ..models.onnx_converter import ONNXConverter, ONNXConversionError
from ..models.onnx_optimizer import ONNXOptimizer


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for export command."""
    parser = argparse.ArgumentParser(
        prog='edge-detection export',
        description='Export PyTorch models to ONNX format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  edge-detection export --model yolov8n.pt --format onnx

  # With specific opset version
  edge-detection export --model yolov8n.pt --format onnx --opset 17

  # With dynamic batch size
  edge-detection export --model yolov8n.pt --format onnx --dynamic-batch

  # With optimization
  edge-detection export --model yolov8n.pt --format onnx --optimize all

  # Custom output directory
  edge-detection export --model yolov8n.pt --format onnx --output-dir ./models
        """
    )

    parser.add_argument(
        '--model',
        required=True,
        help='Path to PyTorch model file (.pt)'
    )
    parser.add_argument(
        '--format',
        choices=['onnx'],
        default='onnx',
        help='Output format (default: onnx)'
    )
    parser.add_argument(
        '--opset',
        type=int,
        default=17,
        help='ONNX opset version (default: 17, recommended: 17)'
    )
    parser.add_argument(
        '--dynamic-batch',
        action='store_true',
        help='Enable dynamic batch size support'
    )
    parser.add_argument(
        '--optimize',
        choices=['none', 'basic', 'all'],
        default='all',
        help='Optimization level (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for ONNX model (default: ~/.cache/edge-detection/models/onnx/)'
    )
    parser.add_argument(
        '--output-name',
        help='Output model name (default: same as input model)'
    )

    return parser


def main(args):
    """Execute export command."""
    print("=" * 60)
    print("🔄 Edge Detection Model Export")
    print("=" * 60)
    print()

    # Validate model file
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Error: Model file not found: {args.model}")
        sys.exit(1)

    print(f"📦 Input model: {args.model}")
    print(f"📤 Output format: {args.format}")
    print(f"🔢 Opset version: {args.opset}")

    if args.dynamic_batch:
        print("✨ Dynamic batch: Enabled")

    print(f"⚡ Optimization: {args.optimize}")
    print()

    # Determine output name
    if args.output_name:
        output_name = args.output_name
    else:
        output_name = model_path.stem

    try:
        # Initialize converter
        print("🔧 Initializing ONNX converter...")
        converter = ONNXConverter(
            output_dir=args.output_dir,
            opset_version=args.opset
        )

        # Convert model
        print()
        onnx_path = converter.convert(
            model_path=str(model_path),
            model_name=output_name,
            dynamic_batch=args.dynamic_batch,
            optimize=(args.optimize != 'none')
        )

        # Apply additional optimization if requested
        if args.optimize in ['basic', 'all']:
            print()
            print("🚀 Applying graph optimizations...")
            optimizer = ONNXOptimizer()

            optimizer.optimize(
                model_path=str(onnx_path),
                level=args.optimize
            )

        print()
        print("=" * 60)
        print("✅ Export Complete!")
        print("=" * 60)
        print()
        print(f"📁 ONNX model: {onnx_path}")

        # Get model info
        size_mb = converter.get_model_size(str(onnx_path))
        print(f"📦 Model size: {size_mb:.2f} MB")

        info = converter.get_conversion_info(str(onnx_path))
        if 'error' not in info:
            print(f"🔢 Opset version: {info['opset_version']}")
            print(f"🔨 Graph nodes: {info['num_nodes']}")
            print(f"📊 Inputs: {', '.join(info['graph_inputs'])}")
            print(f"📊 Outputs: {', '.join(info['graph_outputs'])}")

        print()
        print("💡 Usage:")
        print(f"   edge-detection detect --model {onnx_path} --device onnx --input image.jpg")
        print()

        return 0

    except ONNXConversionError as e:
        print()
        print(str(e))
        print()
        return 1

    except KeyboardInterrupt:
        print()
        print("⚠️  Export cancelled by user")
        print()
        return 130

    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    sys.exit(main(args))
