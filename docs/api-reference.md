# API Reference

Complete API reference for the Real-time Edge Detection library.

## Table of Contents

- [Detection API](#detection-api)
- [Device Management](#device-management)
- [Configuration](#configuration)
- [Batch Processing](#batch-processing)
- [Output Formats](#output-formats)
- [Error Handling](#error-handling)
- [Metrics Collection](#metrics-collection)

---

## Detection API

### YOLODetector

Main detector class for YOLO-based object detection.

```python
from src.models.yolo_detector import YOLODetector
from src.hardware.device_manager import DeviceManager

# Initialize detector
device_manager = DeviceManager(device='cpu')
detector = YOLODetector(
    model_path='yolov8n.pt',
    device_manager=device_manager
)

# Run detection
image = cv2.imread('image.jpg')
results = detector.detect(image)
```

#### Parameters

- **model_path** (`str`): Path to YOLO model file (e.g., 'yolov8n.pt')
- **device_manager** (`DeviceManager`): Device manager for hardware acceleration
- **confidence_threshold** (`float`, optional): Confidence threshold (0.0-1.0). Default: 0.5
- **iou_threshold** (`float`, optional): IOU threshold for NMS (0.0-1.0). Default: 0.4
- **max_detections** (`int`, optional): Maximum number of detections. Default: 100

#### Methods

##### detect(image: np.ndarray) -> List[Dict]

Detect objects in an image.

**Parameters:**
- `image` (`np.ndarray`): Input image as numpy array (H, W, 3) in BGR format

**Returns:**
- `List[Dict]`: List of detection results, each containing:
  - `bbox` (`List[int]`): Bounding box [x1, y1, x2, y2]
  - `confidence` (`float`): Confidence score (0.0-1.0)
  - `class_id` (`int`): Class ID
  - `class_name` (`str`): Class label

**Raises:**
- `ValueError`: If image is invalid or empty
- `RuntimeError`: If model fails to load or inference fails

**Example:**

```python
import cv2
from src.models.yolo_detector import YOLODetector
from src.hardware.device_manager import DeviceManager

# Initialize
device_manager = DeviceManager(device='cpu')
detector = YOLODetector(
    model_path='yolov8n.pt',
    confidence_threshold=0.7,
    device_manager=device_manager
)

# Load and detect
image = cv2.imread('test.jpg')
results = detector.detect(image)

# Process results
for detection in results:
    x1, y1, x2, y2 = detection['bbox']
    confidence = detection['confidence']
    class_name = detection['class_name']

    print(f"Found {class_name} at {x1},{y1} with {confidence:.2f} confidence")
```

---

### ONNXDetector

ONNX Runtime-based detector for optimized inference.

```python
from src.models.onnx import ONNXDetector

detector = ONNXDetector(
    model_path='yolov8n.onnx',
    providers=['CPUExecutionProvider']
)

results = detector.detect(image)
```

#### Parameters

- **model_path** (`str`): Path to ONNX model file
- **providers** (`List[str]`, optional): ONNX execution providers. Default: ['CPUExecutionProvider']
- **confidence_threshold** (`float`, optional): Confidence threshold. Default: 0.5
- **iou_threshold** (`float`, optional): IOU threshold. Default: 0.4

#### Methods

##### detect(image: np.ndarray) -> List[Dict]

Same interface as YOLODetector.

**Example:**

```python
from src.models.onnx import ONNXDetector

# Initialize with CUDA provider if available
detector = ONNXDetector(
    model_path='yolov8n.onnx',
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)

results = detector.detect(image)
```

---

## Device Management

### DeviceManager

Manages device selection and hardware acceleration.

```python
from src.hardware.device_manager import DeviceManager

# Auto-detect best device
device_manager = DeviceManager(device='auto')

# Force CPU
device_manager = DeviceManager(device='cpu')

# Force CUDA (if available)
device_manager = DeviceManager(device='cuda')
```

#### Parameters

- **device** (`str`): Device selection ('auto', 'cpu', 'cuda', 'mps')

#### Properties

- **device** (`torch.device`): PyTorch device object
- **device_type** (`str`): Device type string
- **is_available** (`bool`): Whether device is available

#### Methods

##### get_device_info() -> Dict

Get information about the selected device.

**Returns:**
- `Dict`: Device information including name, memory, capabilities

**Example:**

```python
from src.hardware.device_manager import DeviceManager

device_manager = DeviceManager(device='auto')
info = device_manager.get_device_info()

print(f"Using device: {info['type']}")
print(f"Device name: {info.get('name', 'N/A')}")
```

---

## Configuration

### ConfigManager

Manages YAML configuration files with validation.

```python
from src.config.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager('config.yaml')

# Access configuration
model_path = config_manager.get('model.path')
confidence = config_manager.get('detection.confidence_threshold')

# Update configuration
config_manager.set('detection.confidence_threshold', 0.7)
config_manager.save()
```

#### Parameters

- **config_path** (`str`, optional): Path to configuration file

#### Methods

##### load(config_path: str) -> None

Load configuration from YAML file.

##### get(key: str, default=None) -> Any

Get configuration value by dot-notation key.

**Parameters:**
- `key` (`str`): Configuration key (e.g., 'model.path')
- `default` (`Any`, optional): Default value if key not found

**Returns:**
- `Any`: Configuration value

##### set(key: str, value: Any) -> None

Set configuration value by dot-notation key.

##### validate() -> bool

Validate configuration against schema.

**Returns:**
- `bool`: True if valid

**Raises:**
- `ValidationError`: If configuration is invalid

**Example:**

```python
from src.config.config_manager import ConfigManager

# Load and validate
config_manager = ConfigManager('config.yaml')
if not config_manager.validate():
    print("Configuration invalid!")

# Get nested values
model_type = config_manager.get('model.type')
confidence = config_manager.get('detection.confidence_threshold', default=0.5)

# Update values
config_manager.set('detection.iou_threshold', 0.5)
config_manager.save()
```

---

### ProfileManager

Manages configuration profiles (dev, prod, testing).

```python
from src.config.profile_manager import ProfileManager

profile_manager = ProfileManager()

# List available profiles
profiles = profile_manager.list_profiles()

# Load specific profile
config = profile_manager.load_profile('prod')
```

#### Methods

##### list_profiles() -> List[str]

Get list of available profile names.

##### load_profile(profile_name: str) -> Dict

Load configuration for specified profile.

**Parameters:**
- `profile_name` (`str`): Profile name ('dev', 'prod', 'testing')

**Returns:**
- `Dict`: Profile configuration

---

## Batch Processing

### BatchProcessor

Process multiple images in batch with progress tracking.

```python
from src.core.batch_processor import BatchProcessor

processor = BatchProcessor()

# Process list of images
results = processor.process_batch([
    'image1.jpg',
    'image2.jpg',
    'image3.jpg'
])

# Process directory
results = processor.process_directory('./images', recursive=True)
```

#### Parameters

- **detector** (Detector, optional): Detector instance to use
- **batch_size** (`int`, optional): Batch size for processing. Default: 1

#### Methods

##### process_batch(images: List[str]) -> List[Dict]

Process list of image paths.

**Parameters:**
- `images` (`List[str]`): List of image file paths

**Returns:**
- `List[Dict]`: Detection results for each image

##### process_directory(directory: str, recursive: bool = False) -> List[Dict]

Process all images in a directory.

**Parameters:**
- `directory` (`str`): Directory path
- `recursive` (`bool`): Process subdirectories. Default: False

**Returns:**
- `List[Dict]`: Detection results

##### set_progress_callback(callback: Callable) -> None

Set progress callback function.

**Example:**

```python
from src.core.batch_processor import BatchProcessor

processor = BatchProcessor()

def on_progress(current, total, filename):
    percent = (current / total) * 100
    print(f"Processing {filename}: {percent:.0f}%")

processor.set_progress_callback(on_progress)

results = processor.process_batch(['img1.jpg', 'img2.jpg'])
```

---

## Output Formats

### JSONOutput

Export detection results to JSON format.

```python
from src.cli.output import JSONOutput

exporter = JSONOutput('output.json')
exporter.export({
    'image1.jpg': detection_results_1,
    'image2.jpg': detection_results_2
})
```

#### Output Format

```json
{
  "image1.jpg": [
    {
      "bbox": [100, 100, 200, 200],
      "confidence": 0.85,
      "class_id": 0,
      "class_name": "person"
    }
  ]
}
```

---

### CSVOutput

Export detection results to CSV format.

```python
from src.cli.output import CSVOutput

exporter = CSVOutput('output.csv')
exporter.export(results)
```

#### Output Format

```csv
image,bbox_x1,bbox_y1,bbox_x2,bbox_y2,confidence,class_id,class_name
image1.jpg,100,100,200,200,0.85,0,person
```

---

### COCOOutput

Export detection results in COCO format.

```python
from src.cli.output import COCOOutput

exporter = COCOOutput('coco.json')
exporter.export(results)
```

#### Output Format

Standard COCO JSON format with `images`, `annotations`, and `categories` arrays.

---

## Error Handling

### Exceptions

#### DetectionError

Base exception for detection errors.

```python
from src.core.errors import DetectionError

try:
    results = detector.detect(image)
except DetectionError as e:
    print(f"Detection failed: {e}")
```

#### ModelLoadError

Raised when model fails to load.

```python
from src.core.errors import ModelLoadError

try:
    detector = YOLODetector(model_path='invalid.pt')
except ModelLoadError as e:
    print(f"Model loading failed: {e}")
```

#### DeviceError

Raised when device initialization fails.

```python
from src.core.errors import DeviceError

try:
    device_manager = DeviceManager(device='invalid_device')
except DeviceError as e:
    print(f"Device error: {e}")
```

#### ValidationError

Raised when configuration validation fails.

```python
from src.core.errors import ValidationError

try:
    config_manager.validate()
except ValidationError as e:
    print(f"Configuration invalid: {e}")
```

---

## Metrics Collection

### MetricsManager

Collect and export performance metrics.

```python
from src.metrics.manager import MetricsManager

metrics_manager = MetricsManager()

# Record detection latency
metrics_manager.record_latency(detector, image)

# Get metrics summary
summary = metrics_manager.get_summary()
print(f"Average latency: {summary['avg_latency_ms']:.2f}ms")
```

#### Methods

##### record_latency(detector, image) -> None

Record detection latency.

##### get_summary() -> Dict

Get metrics summary including latency, throughput, memory usage.

---

## CLI API

### Main Commands

```bash
# Basic detection
edge-detection detect image.jpg

# Video detection with interactive mode
edge-detection detect video.mp4 --interactive

# Export to JSON
edge-detection detect image.jpg --output results.json --output-format json

# Batch processing
edge-detection detect-batch *.jpg --output-dir results

# Configuration validation
edge-detection config validate --config config.yaml

# Run benchmarks
edge-detection benchmark --iterations 100
```

### CLI Options

- `--config`: Path to configuration file
- `--profile`: Configuration profile (dev/prod/testing)
- `--model`: Override model path
- `--confidence`: Override confidence threshold
- `--iou`: Override IOU threshold
- `--device`: Device selection (auto/cpu/cuda/mps)
- `--output-format`: Output format (json/csv/coco/visual)
- `--metrics`: Enable metrics (none/prometheus)

---

## Type Hints

The library uses Python type hints throughout. Key types:

```python
from typing import List, Dict, Any, Optional, Callable
import numpy as np

DetectionResult = Dict[str, Any]
# {
#     'bbox': List[int],
#     'confidence': float,
#     'class_id': int,
#     'class_name': str
# }

DetectionResults = List[DetectionResult]

Image = np.ndarray  # Shape: (H, W, 3), dtype: uint8

ProgressCallback = Callable[[int, int, str], None]
# (current, total, filename) -> None
```

---

## Best Practices

### 1. Always use DeviceManager for device selection

```python
# Good
device_manager = DeviceManager(device='auto')
detector = YOLODetector(model_path='yolov8n.pt', device_manager=device_manager)

# Bad - hardcoded device
detector = YOLODetector(model_path='yolov8n.pt', device='cpu')
```

### 2. Validate images before detection

```python
def validate_image(image):
    if image is None or image.size == 0:
        raise ValueError("Invalid image")
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError("Image must be 3-channel BGR")
    return True

image = cv2.imread('test.jpg')
if validate_image(image):
    results = detector.detect(image)
```

### 3. Use batch processing for multiple images

```python
# Good - efficient batch processing
processor = BatchProcessor()
results = processor.process_batch(image_list)

# Bad - sequential processing
results = [detector.detect(cv2.imread(img)) for img in image_list]
```

### 4. Handle errors gracefully

```python
from src.core.errors import DetectionError, ModelLoadError

try:
    detector = YOLODetector(model_path='yolov8n.pt')
    results = detector.detect(image)
except ModelLoadError as e:
    logger.error(f"Failed to load model: {e}")
    # Fallback to alternative model or exit
except DetectionError as e:
    logger.error(f"Detection failed: {e}")
    # Handle detection error
```

### 5. Clean up resources

```python
# Process images
detector = YOLODetector(model_path='yolov8n.pt')

# ... do processing ...

# Clean up (important for GPU memory)
del detector
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

---

## Version Compatibility

The library maintains backward compatibility within major versions:

- **1.x.x**: Stable API
- **0.x.x**: Development versions (API may change)

When upgrading, check the changelog for breaking changes.

---

## Support

For issues, questions, or contributions:
- GitHub Issues: [Project Repository]
- Documentation: [Online Docs]
- Examples: `examples/` directory
