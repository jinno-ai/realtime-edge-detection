#!/usr/bin/env python3
"""
CLI Tool for Real-time Edge Detection

Usage:
    python run.py detect image.jpg
    python run.py webcam
    python run.py video input.mp4
    python run.py benchmark
"""

import argparse
import sys
import cv2
import time

from src.models.yolo_detector import YOLODetector
from src.preprocessing.image_processor import ImageProcessor
from src.config.config_manager import ConfigManager


def create_detector(args):
    """
    Create YOLODetector with configuration.

    Priority:
    1. Config file (if --config specified)
    2. Profile (if --profile specified)
    3. Default configuration
    4. Command-line args (overrides all config)
    """
    from src.core.config import ConfigManager

    # Load configuration
    if hasattr(args, 'config') and args.config:
        config_manager = ConfigManager(config_path=args.config)
    elif hasattr(args, 'profile') and args.profile:
        config_manager = ConfigManager(profile=args.profile)
    else:
        config_manager = ConfigManager()

    # Load and get the config dict
    config = config_manager.load_config()

    # Apply command-line overrides
    if hasattr(args, 'model') and args.model:
        config['model']['path'] = args.model
    if hasattr(args, 'confidence') and args.confidence is not None:
        config['detection']['confidence_threshold'] = args.confidence
    if hasattr(args, 'iou') and args.iou is not None:
        config['detection']['iou_threshold'] = args.iou

    # Create detector with config
    return YOLODetector(config=config)


def detect_command(args):
    """Detect objects in image"""
    print("🔧 Initializing detector...")
    detector = create_detector(args)

    print("🧠 Loading model...")
    detector.load_model()

    # Load image
    print(f"📸 Loading image: {args.image}")
    image = cv2.imread(args.image)

    if image is None:
        print(f"❌ Error: Could not load image")
        sys.exit(1)

    # Detect
    print("🔍 Detecting objects...")
    start_time = time.time()
    detections = detector.detect(image)
    inference_time = time.time() - start_time

    # Results
    print(f"\n✅ Found {len(detections)} objects in {inference_time*1000:.1f}ms")

    if detections:
        print("\n📊 Detections:")
        for i, det in enumerate(detections, 1):
            print(f"   {i}. {det['class_name']}: {det['confidence']:.3f}")

    # Draw and save
    if args.output:
        result = detector.draw_detections(image, detections)
        cv2.imwrite(args.output, result)
        print(f"\n💾 Saved result to: {args.output}")

    # Show if requested
    if args.show:
        result = detector.draw_detections(image, detections)
        cv2.imshow("Detections", result)
        print("\n Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def webcam_command(args):
    """Run real-time webcam detection"""
    print("🔧 Initializing detector...")
    detector = create_detector(args)

    print("🧠 Loading model...")
    detector.load_model()

    # Open webcam
    print(f"📹 Opening webcam (index {args.camera})...")
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        sys.exit(1)

    print("✅ Webcam opened!")
    print("Press 'q' to quit\n")

    frame_count = 0
    total_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect
            start_time = time.time()
            detections = detector.detect(frame)
            inference_time = time.time() - start_time

            # Draw
            frame = detector.draw_detections(frame, detections)

            # FPS
            fps = 1 / inference_time if inference_time > 0 else 0
            frame_count += 1
            total_time += inference_time
            avg_fps = frame_count / total_time if total_time > 0 else 0

            # Add info
            cv2.putText(
                frame,
                f"FPS: {fps:.1f} (Avg: {avg_fps:.1f}) | Objects: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Display
            cv2.imshow("YOLO Detection", frame)

            # Quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n📊 Processed {frame_count} frames")
        print(f"   Average FPS: {avg_fps:.1f}")


def video_command(args):
    """Process video file"""
    print("🔧 Initializing detector...")
    detector = create_detector(args)

    print("🧠 Loading model...")
    detector.load_model()

    print(f"🎬 Processing video: {args.input}")
    detector.detect_video(args.input, args.output)


def benchmark_command(args):
    """Benchmark detection performance"""
    print("🔧 Initializing detector...")
    detector = create_detector(args)

    print("🧠 Loading model...")
    detector.load_model()

    print(f"\n🏃 Running {args.iterations} iterations...")

    # Create test image
    import numpy as np
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    times = []
    for i in range(args.iterations):
        start = time.time()
        detections = detector.detect(test_image)
        elapsed = time.time() - start
        times.append(elapsed)

        if (i + 1) % 10 == 0:
            print(f"   Progress: {i + 1}/{args.iterations}")

    # Statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    avg_fps = 1 / avg_time

    print("\n" + "=" * 60)
    print("📊 Benchmark Results")
    print("=" * 60)
    print(f"\n   Iterations: {args.iterations}")
    print(f"   Avg Time: {avg_time*1000:.2f}ms")
    print(f"   Min Time: {min_time*1000:.2f}ms")
    print(f"   Max Time: {max_time*1000:.2f}ms")
    print(f"   Avg FPS: {avg_fps:.2f}")


def preprocess_command(args):
    """Test image preprocessing"""
    print("🔧 Testing image preprocessing...")

    processor = ImageProcessor(target_size=(640, 640))

    # Load image
    image = cv2.imread(args.image)
    if image is None:
        print(f"❌ Error: Could not load image")
        sys.exit(1)

    print(f"📸 Original size: {image.shape}")

    # Letterbox
    padded, scale, padding = processor.letterbox(image)
    print(f"✅ Letterbox: {padded.shape}, scale: {scale:.3f}, padding: {padding}")

    # Preprocess
    preprocessed = processor.preprocess(image)
    print(f"✅ Preprocessed: {preprocessed.shape}")


def export_command(args):
    """Export model to ONNX format"""
    from src.commands.export import main as export_main
    return export_main(args)


def quantize_command(args):
    """Quantize model for optimized inference"""
    from src.commands.quantize import main as quantize_main
    return quantize_main(args)


def main():
    parser = argparse.ArgumentParser(
        description="Real-time Edge Detection CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py detect image.jpg
  python run.py detect image.jpg --show --output result.jpg
  python run.py webcam
  python run.py webcam --model yolov8n.pt --confidence 0.6
  python run.py video input.mp4 --output output.mp4
  python run.py benchmark --iterations 100
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Common arguments for all commands
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument('--config', help='Path to configuration file (YAML)')
    common_args.add_argument('--profile', help='Configuration profile (dev/prod/testing)')
    common_args.add_argument('--model', help='Model path (overrides config)')
    common_args.add_argument('--confidence', type=float, help='Confidence threshold (overrides config)')
    common_args.add_argument('--iou', type=float, help='IOU threshold (overrides config)')

    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Detect objects in image', parents=[common_args])
    detect_parser.add_argument('image', help='Input image path')
    detect_parser.add_argument('--output', help='Output image path')
    detect_parser.add_argument('--show', action='store_true', help='Display result')

    # Webcam command
    webcam_parser = subparsers.add_parser('webcam', help='Real-time webcam detection', parents=[common_args])
    webcam_parser.add_argument('--camera', type=int, default=0, help='Camera index')

    # Video command
    video_parser = subparsers.add_parser('video', help='Process video file', parents=[common_args])
    video_parser.add_argument('input', help='Input video path')
    video_parser.add_argument('--output', default='output.mp4', help='Output video path')

    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Benchmark performance', parents=[common_args])
    bench_parser.add_argument('--iterations', type=int, default=100, help='Number of iterations')

    # Preprocess command
    pre_parser = subparsers.add_parser('preprocess', help='Test image preprocessing')
    pre_parser.add_argument('image', help='Input image path')

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export model to ONNX format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py export --model yolov8n.pt --format onnx
  python run.py export --model yolov8n.pt --format onnx --opset 17
  python run.py export --model yolov8n.pt --format onnx --dynamic-batch
        """
    )
    export_parser.add_argument('--model', required=True, help='Path to PyTorch model')
    export_parser.add_argument('--format', choices=['onnx'], default='onnx', help='Output format')
    export_parser.add_argument('--opset', type=int, default=17, help='ONNX opset version')
    export_parser.add_argument('--dynamic-batch', action='store_true', help='Enable dynamic batch')
    export_parser.add_argument('--optimize', choices=['none', 'basic', 'all'], default='all', help='Optimization level')
    export_parser.add_argument('--output-dir', help='Output directory')
    export_parser.add_argument('--output-name', help='Output model name')

    # Quantize command
    quantize_parser = subparsers.add_parser(
        'quantize',
        help='Quantize model for optimized inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py quantize --model yolov8n.pt --format int8
  python run.py quantize --model yolov8n.pt --format fp16
  python run.py quantize --model yolov8n.pt --format int8 --skip-validation
  python run.py quantize --model yolov8n.pt --format int8 --output ./models/yolov8n.int8.pt
        """
    )
    quantize_parser.add_argument('--model', required=True, help='Path to PyTorch model file (.pt)')
    quantize_parser.add_argument('--format', choices=['int8', 'fp16'], default='int8', help='Quantization format')
    quantize_parser.add_argument('--backend', choices=['pytorch', 'tensorrt', 'onnx'], default='pytorch', help='Quantization backend')
    quantize_parser.add_argument('--output', help='Output path for quantized model')
    quantize_parser.add_argument('--calib-data', help='Path to calibration dataset for INT8')
    quantize_parser.add_argument('--skip-validation', action='store_true', help='Skip accuracy validation')
    quantize_parser.add_argument('--force', action='store_true', help='Force quantization even if accuracy degradation exceeds threshold')

    args = parser.parse_args()

    if args.command == 'detect':
        detect_command(args)
    elif args.command == 'webcam':
        webcam_command(args)
    elif args.command == 'video':
        video_command(args)
    elif args.command == 'benchmark':
        benchmark_command(args)
    elif args.command == 'preprocess':
        preprocess_command(args)
    elif args.command == 'export':
        export_command(args)
    elif args.command == 'quantize':
        quantize_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
