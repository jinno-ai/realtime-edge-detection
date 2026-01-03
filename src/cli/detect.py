"""
Detection command implementation.

This module implements the core detection logic, integrating configuration
management, model loading, device selection, and output formatting.
"""

import click
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from src.config.config_manager import ConfigManager
from src.models.model_manager import ModelManager
from src.hardware.device_manager import DeviceManager as HardwareDeviceManager
from src.cli.metrics import MetricsTracker
from src.cli.output import OutputHandler
from src.cli.interactive import run_interactive_detection
from src.detection.factory import DetectorFactory
from src.metrics.manager import MetricsManager


def create_detector(ctx, model, confidence, iou, device):
    """
    Create detector with integrated configuration.

    Args:
        ctx: Click context
        model: Override model path
        confidence: Override confidence threshold
        iou: Override IOU threshold
        device: Override device selection

    Returns:
        Tuple of (config, model_path, device_manager)
    """
    try:
        # Load configuration
        config_mgr = ConfigManager(
            config_path=ctx.obj.get('config'),
            profile=ctx.obj.get('profile')
        )

        # Apply CLI overrides
        if model:
            config_mgr.config['model']['path'] = model
        if confidence is not None:
            config_mgr.config['detection']['confidence_threshold'] = confidence
        if iou is not None:
            config_mgr.config['detection']['iou_threshold'] = iou
        if device:
            config_mgr.config['device']['type'] = device

        # Validate configuration
        config_mgr.validate()

        # Initialize managers
        model_mgr = ModelManager()

        # Get device from config or CLI override (AC: #2, #4)
        device_str = config_mgr.get('device.type', default='auto')

        # Create device manager with device string
        device_mgr = HardwareDeviceManager(device_str=device_str)

        # Validate device availability (AC: #3)
        try:
            device_mgr.validate_device()
        except RuntimeError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

        # Get device info for logging (AC: #1, #5)
        device_info = device_mgr.get_device_info()

        # Display device selection (AC: #1, #2)
        if device_str == 'auto':
            click.echo(f"Auto-detected device: {device_mgr.device_string} ({device_info.get('name', 'CPU')})")
        elif device_str == 'cpu':
            click.echo(f"Using device: cpu (forced)")
        else:
            click.echo(f"Using device: {device_mgr.device_string}")

        # Show multi-GPU info if applicable (AC: #5)
        if device_mgr.selected_device.value == 'cuda' and device_info.get('gpu_count', 0) > 1:
            click.echo(f"Available GPUs: {device_info['gpu_count']}")
            for i, gpu_info in enumerate(device_info.get('gpus', [])):
                click.echo(f"  - cuda:{i} ({gpu_info['name']}, {gpu_info['memory_gb']}GB)")

        # Get model path (download if needed)
        model_name = config_mgr.get('model.path')
        model_path = model_mgr.get_model(model_name)

        if ctx.obj.get('verbose'):
            click.echo(f"Model: {model_path}")
            click.echo(f"Confidence: {config_mgr.get('detection.confidence_threshold')}")
            click.echo(f"IOU: {config_mgr.get('detection.iou_threshold')}")

        return config_mgr, model_path, device_mgr

    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error initializing detector: {e}", err=True)
        raise SystemExit(1)


def run_detect(ctx, input, output, output_format, interactive,
               model, confidence, iou, device, batch, benchmark, metrics_mode='none'):
    """
    Run detection on input file.

    Args:
        ctx: Click context
        input: Input file path
        output: Output file path
        output_format: Output format (json/csv/coco/visual)
        interactive: Enable interactive mode
        model: Override model path
        confidence: Override confidence threshold
        iou: Override IOU threshold
        device: Override device selection
        batch: Batch processing flag
        benchmark: Benchmark mode flag
        metrics_mode: Metrics collection mode ('none', 'prometheus')
    """
    input_path = Path(input)

    # Validate input file
    if not input_path.exists():
        click.echo(f"Error: Input file does not exist: {input}", err=True)
        raise SystemExit(1)

    # Create detector
    config_mgr, model_path, device_mgr = create_detector(
        ctx, model, confidence, iou, device
    )

    # Create detector using factory
    try:
        # Get model type from model path for factory
        model_type = config_mgr.get('model.path')

        # Create detector instance
        detector = DetectorFactory.create_detector(model_type)

        # Get torch device from device manager
        torch_device = device_mgr.get_torch_device()

        # Load model with device
        detector.load_model(str(model_path), torch_device)

        if ctx.obj.get('verbose'):
            from src.detection.base import ModelInfo
            model_info: ModelInfo = detector.get_model_info()
            click.echo(f"  Detector Type: {type(detector).__name__}")
            click.echo(f"  Model Name: {model_info.name}")
            if model_info.version:
                click.echo(f"  Model Version: {model_info.version}")
            if model_info.input_size:
                click.echo(f"  Input Size: {model_info.input_size}")
            if model_info.class_names:
                click.echo(f"  Classes: {len(model_info.class_names)}")

    except Exception as e:
        click.echo(f"Error loading detector: {e}", err=True)
        raise SystemExit(1)

    # Initialize metrics manager
    metrics_manager = MetricsManager(mode=metrics_mode)

    # Start Prometheus server if enabled
    if metrics_mode == 'prometheus':
        try:
            metrics_manager.start_prometheus_server()
            click.echo(f"Prometheus metrics available at http://localhost:9090/metrics")
        except Exception as e:
            click.echo(f"Warning: Could not start Prometheus server: {e}", err=True)

    # Process input based on type
    try:
        if interactive:
            # Interactive mode
            run_interactive_detection(detector, input_path, config_mgr, metrics_manager)
        else:
            # Single file detection
            if input_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                # Image
                results = process_image(detector, input_path, metrics_manager)
            elif input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                # Video
                results = process_video(detector, input_path, metrics_manager)
            else:
                click.echo(f"Error: Unsupported file type: {input_path.suffix}", err=True)
                raise SystemExit(1)

            # Handle output
            handle_output(results, input_path, output, output_format, config_mgr)

            # Display metrics
            stats = metrics_manager.get_stats()
            click.echo(metrics_manager.format_stats(stats))

    finally:
        # Cleanup metrics manager
        metrics_manager.cleanup()


def process_image(detector, image_path: Path, metrics_manager: MetricsManager) -> Dict:
    """
    Process single image for detection.

    Args:
        detector: AbstractDetector instance
        image_path: Path to input image
        metrics_manager: Metrics manager

    Returns:
        Dictionary with detection results
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        click.echo(f"Error: Could not load image: {image_path}", err=True)
        raise SystemExit(1)

    # Convert BGR to RGB (AbstractDetector expects RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run detection
    metrics_manager.start_inference()
    try:
        result = detector.detect(image_rgb)
        inference_time = metrics_manager.end_inference()
    except Exception as e:
        metrics_manager.record_error()
        raise

    # Parse results from DetectionResult
    detections = parse_detection_result(result, detector)

    return {
        'image': image,
        'detections': detections,
        'inference_time': inference_time
    }


def process_video(detector, video_path: Path, metrics_manager: MetricsManager) -> Dict:
    """
    Process video for detection.

    Args:
        detector: AbstractDetector instance
        video_path: Path to input video
        metrics_manager: Metrics manager

    Returns:
        Dictionary with detection results
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        click.echo(f"Error: Could not open video: {video_path}", err=True)
        raise SystemExit(1)

    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    all_detections = []

    click.echo(f"Processing video: {total_frames} frames at {fps:.2f} FPS")

    # Process frames with progress bar
    from tqdm import tqdm

    with tqdm(total=total_frames, desc="Detecting", unit="frames") as pbar:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Run detection
            metrics_manager.start_inference()
            try:
                result = detector.detect(frame_rgb)
                inference_time = metrics_manager.end_inference()
            except Exception as e:
                metrics_manager.record_error()
                raise

            # Parse results from DetectionResult
            detections = parse_detection_result(result, detector)
            all_detections.extend(detections)

            # Update progress bar
            pbar.set_postfix({
                'FPS': f'{1.0/inference_time:.1f}' if inference_time > 0 else 'N/A',
                'Objects': len(detections)
            })
            pbar.update(1)

            frame_count += 1

            # Limit for testing
            if frame_count >= 1000:  # Safety limit
                click.echo("\nWarning: Reached frame limit (1000)", err=True)
                break

    cap.release()

    return {
        'detections': all_detections,
        'total_frames': frame_count
    }


def parse_yolo_results(results, image_shape) -> list:
    """
    Parse YOLO results into standard format.

    Args:
        results: YOLO results object
        image_shape: Shape of original image (h, w, c)

    Returns:
        List of detection dictionaries
    """
    detections = []

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            # Get confidence and class
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = result.names[class_id]

            detections.append({
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'confidence': confidence,
                'class_id': class_id,
                'class_name': class_name
            })

    return detections


def parse_detection_result(result, detector) -> list:
    """
    Parse DetectionResult into standard format.

    Args:
        result: DetectionResult from AbstractDetector
        detector: AbstractDetector instance (for getting class names)

    Returns:
        List of detection dictionaries
    """
    from src.detection.base import DetectionResult

    if not isinstance(result, DetectionResult):
        raise TypeError(f"Expected DetectionResult, got {type(result)}")

    # Get model info for class names
    model_info = detector.get_model_info()
    class_names = model_info.class_names or []

    detections = []

    for i in range(len(result.boxes)):
        box = result.boxes[i]
        confidence = float(result.scores[i])
        class_id = int(result.classes[i])

        # Get class name
        class_name = class_names[class_id] if class_id < len(class_names) else f"class_{class_id}"

        detections.append({
            'bbox': box.tolist(),
            'confidence': confidence,
            'class_id': class_id,
            'class_name': class_name
        })

    return detections


def handle_output(results: Dict, input_path: Path, output: Optional[str],
                  output_format: str, config_mgr: ConfigManager) -> None:
    """
    Handle output formatting and saving.

    Args:
        results: Detection results
        input_path: Input file path
        output: Output file path (optional)
        output_format: Output format
        config_mgr: Configuration manager
    """
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Generate default output path
        output_path = Path('output') / f"{input_path.stem}_detections"
        if output_format == 'visual':
            output_path = output_path.with_suffix('.jpg')
        elif output_format == 'json':
            output_path = output_path.with_suffix('.json')
        elif output_format == 'csv':
            output_path = output_path.with_suffix('.csv')
        elif output_format == 'coco':
            output_path = output_path.with_suffix('.json')

    detections = results.get('detections', [])

    # Prepare metadata
    metadata = {
        'model': str(config_mgr.get('model.path')),
        'device': str(config_mgr.get('device.type')),
        'confidence_threshold': config_mgr.get('detection.confidence_threshold'),
        'iou_threshold': config_mgr.get('detection.iou_threshold'),
        'input_file': str(input_path)
    }

    # Export based on format
    if output_format == 'json':
        OutputHandler.to_json(detections, metadata, output_path)
        click.echo(f"Results saved to: {output_path}")

    elif output_format == 'csv':
        OutputHandler.to_csv(detections, output_path)
        click.echo(f"Results saved to: {output_path}")

    elif output_format == 'coco':
        image_info = {
            'filename': input_path.name,
            'width': results.get('image', np.zeros((0, 0, 0))).shape[1] if 'image' in results else 0,
            'height': results.get('image', np.zeros((0, 0, 0))).shape[0] if 'image' in results else 0
        }
        OutputHandler.to_coco(detections, image_info, output_path)
        click.echo(f"Results saved to: {output_path}")

    elif output_format == 'visual':
        if 'image' in results:
            OutputHandler.to_visual(results['image'], detections, output_path)
            click.echo(f"Annotated image saved to: {output_path}")
        else:
            click.echo("Warning: Visual output not available for video processing", err=True)


def handle_config_command(action: str, config: Optional[str]) -> None:
    """
    Handle configuration management commands.

    Args:
        action: Action to perform (validate/show/list-profiles)
        config: Config file path
    """
    if action == 'validate':
        if not config:
            click.echo("Error: --config option required for validate action", err=True)
            raise SystemExit(1)

        try:
            config_mgr = ConfigManager(config_path=Path(config))
            config_mgr.validate()
            click.echo(f"✓ Configuration file is valid: {config}")
        except Exception as e:
            click.echo(f"✗ Configuration validation failed: {e}", err=True)
            raise SystemExit(1)

    elif action == 'show':
        config_mgr = ConfigManager(config_path=Path(config) if config else None)
        click.echo("\nCurrent Configuration:")
        click.echo(f"  Model: {config_mgr.get('model.path')}")
        click.echo(f"  Device: {config_mgr.get('device.type')}")
        click.echo(f"  Confidence: {config_mgr.get('detection.confidence_threshold')}")
        click.echo(f"  IOU: {config_mgr.get('detection.iou_threshold')}")

    elif action == 'list-profiles':
        config_dir = Path('config')
        if config_dir.exists():
            profiles = [f.stem for f in config_dir.glob('*.yaml')
                       if f.stem not in ['default', 'example']]
            click.echo("\nAvailable Profiles:")
            for profile in profiles:
                click.echo(f"  - {profile}")
        else:
            click.echo("No configuration profiles found")
