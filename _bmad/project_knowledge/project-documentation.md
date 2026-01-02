# Realtime Edge Detection - Project Documentation

**Generated:** 2026-01-03
**Project Type:** Python Backend / Computer Vision
**Documentation Mode:** Initial Scan
**Author:** BMad Documentation Workflow

---

## Project Overview

**Realtime Edge Detection** is a Python-based computer vision project focused on real-time object detection using YOLO (You Only Look Once) models. The project provides edge-optimized detection capabilities with configurable preprocessing, augmentation, and video processing utilities.

### Key Characteristics

- **Language:** Python 3.14+
- **Framework:** pytest for testing, OpenCV for image processing
- **Primary Domain:** Computer Vision / Object Detection
- **Deployment Target:** Edge devices (real-time processing requirements)
- **Architecture Pattern:** Modular pipeline architecture with configurable components

### Project Purpose

Enable real-time object detection on edge devices with:
- Optimized image preprocessing and augmentation
- Configurable YOLO model integration
- Video stream processing
- Edge device optimization (quantization, resolution reduction)

---

## Technology Stack

### Core Dependencies

**Computer Vision & Image Processing:**
- `opencv-python` (cv2) - Image and video I/O, preprocessing
- `numpy` - Numerical operations, array manipulation
- `ultralytics` - YOLO v8 model inference

**Configuration:**
- `pyyaml` - YAML configuration file management
- Custom ConfigManager for hierarchical configuration

**Testing:**
- `pytest` - Test framework
- `pytest-cov` - Code coverage reporting
- `pytest-black` - Code style checking
- `pytest-anyio` - Async test support

**Development:**
- Standard Python tooling (setuptools, wheel, build)

### Development Tools

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_image_processor.py -v
```

---

## Project Structure

```
realtime-edge-detection/
├── src/                          # Source code
│   ├── __init__.py
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── config_manager.py     # ConfigManager class with YAML/Env/CLI support
│   ├── core/                     # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py             # Legacy config (deprecated)
│   │   └── errors.py             # Custom exceptions
│   ├── models/                   # Detection models
│   │   ├── __init__.py
│   │   └── yolo_detector.py      # YOLO v8 detector implementation
│   ├── preprocessing/            # Image processing pipeline
│   │   ├── __init__.py
│   │   └── image_processor.py    # ImageProcessor, ImageAugmentor, EdgeOptimizer
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── video_utils.py        # VideoCapture, VideoWriter, FrameProcessor
├── tests/                        # Test suite
│   ├── conftest.py               # Shared fixtures (285 lines)
│   ├── factories/                # Test data factories
│   │   └── __init__.py          # ImageFactory, BBoxFactory, DetectionFactory, etc.
│   ├── integration/              # Integration tests
│   │   └── test_video_processing_integration.py
│   └── unit/                     # Unit tests
│       ├── test_config.py
│       ├── test_image_processor.py    # 29 tests
│       ├── test_video_utils.py        # 26 tests
│       └── test_yolo_detector.py
├── _bmad/                        # BMad framework artifacts
│   ├── bmm/                      # Workflows and config
│   ├── core/                     # Core framework
│   └── output/                   # Generated documentation
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
└── README.md                     # Project documentation
```

---

## Architecture Patterns

### 1. Modular Pipeline Architecture

**Pattern:** Sequential processing stages with configurable components

```
Input Video/Image → Preprocessing → Detection → Post-processing → Output
```

**Key Components:**

1. **ImageProcessor** - Preprocessing pipeline
   - Resize (with/without aspect ratio preservation)
   - Letterbox padding
   - Normalization
   - Batch processing

2. **YOLODetector** - Detection engine
   - Model loading (YOLO v8 via ultralytics)
   - Configurable thresholds (confidence, IOU)
   - Detection result parsing

3. **EdgeOptimizer** - Edge device optimization
   - Quantization (float32 → int8)
   - Resolution reduction
   - Memory layout optimization (contiguous arrays)

4. **FrameProcessor** - Video processing pipeline
   - Stream processing
   - FPS tracking
   - Annotation/drawing

### 2. Configuration Management

**Pattern:** Hierarchical configuration with priority

**Priority (highest to lowest):**
1. CLI arguments
2. Environment variables (`RTEDE_` prefix)
3. YAML configuration file (`config.yaml`)
4. Default values

**Example Usage:**

```python
# Load from file
detector = YOLODetector(config='config.yaml')

# Load with profile
detector = YOLODetector(config=ConfigManager(profile='prod'))

# Use defaults
detector = YOLODetector()
```

### 3. Factory Pattern for Test Data

**Pattern:** Factory classes for generating test data

**Factories Available:**
- `ImageFactory` - Create test images (BGR, RGB, grayscale, batches)
- `BBoxFactory` - Create bounding boxes (random, overlapping)
- `DetectionFactory` - Create detection results
- `VideoFactory` - Create video frame sequences
- `ConfigFactory` - Create test configurations

**Example:**

```python
from tests.factories import ImageFactory

# Create single image
image = ImageFactory.create_bgr(width=640, height=480)

# Create batch
batch = ImageFactory.create_batch(count=10)

# Create with specific color
solid = ImageFactory.create_bgr(color=(255, 0, 0))
```

### 4. Fixture Architecture

**Pattern:** Shared fixtures in conftest.py with auto-cleanup

**Key Fixtures:**
- `sample_image_bgr` - BGR test image
- `sample_images_batch` - Batch of images
- `mock_yolo_model` - Mocked YOLO model
- `temp_config_file` - Temporary YAML config
- `temp_output_dir` - Temporary output directory

---

## API Reference

### YOLODetector

**Purpose:** Real-time object detection using YOLO v8

**Initialization:**

```python
detector = YOLODetector(
    config='config.yaml'  # Path to YAML or ConfigManager instance
)
```

**Key Methods:**

- `load_model()` - Load YOLO model from disk
- `detect(image: np.ndarray) -> List[Dict]` - Detect objects in image
- `detect_video(video_path: str, output_path: str = None)` - Process video file
- `draw_detections(image, detections) -> np.ndarray` - Annotate image

**Detection Result Format:**

```python
{
    'bbox': [x1, y1, x2, y2],  # Bounding box coordinates
    'confidence': 0.85,         # Detection confidence
    'class_id': 0,              # Class ID
    'class_name': 'person'      # Class label
}
```

---

### ImageProcessor

**Purpose:** Image preprocessing for model input

**Initialization:**

```python
processor = ImageProcessor(
    target_size=(640, 640),
    normalize=True,
    mean=(0.485, 0.456, 0.406),
    std=(0.229, 0.224, 0.225)
)
```

**Key Methods:**

- `preprocess(image: np.ndarray) -> np.ndarray` - Full preprocessing pipeline
- `resize(image, size, keep_ratio=False)` - Resize image
- `letterbox(image, target_size)` - Resize with padding
- `batch_preprocess(images: List[np.ndarray]) -> np.ndarray` - Process batch

---

### VideoCapture

**Purpose:** Threaded video capture with buffering

**Initialization:**

```python
cap = VideoCapture(
    source=0,           # Camera index or video file path
    buffer_size=2,      # Frame buffer size
    fps=30             # Target FPS
)

cap.start()  # Start capture thread
frame = cap.read()  # Read frame
cap.stop()   # Stop capture
```

**Key Methods:**

- `start()` - Start background capture thread
- `read() -> np.ndarray` - Read latest frame
- `stop()` - Stop capture and release resources
- `get_fps() -> float` - Calculate actual FPS

---

### EdgeOptimizer

**Purpose:** Optimize images for edge device inference

**Key Methods:**

- `optimize_for_inference(image, quantize=False)` - Memory layout optimization
- `reduce_resolution(image, scale=0.5)` - Downscale for faster inference

---

## Configuration

### Configuration File Structure

```yaml
model:
  type: yolo_v8
  path: yolov8n.pt

detection:
  confidence_threshold: 0.5
  iou_threshold: 0.4
  max_detections: 100

preprocessing:
  target_size: [640, 640]
  normalize: true

# Environment-specific overrides
profiles:
  prod:
    detection:
      confidence_threshold: 0.7
  dev:
    detection:
      confidence_threshold: 0.3
```

### Environment Variables

```bash
# Override config values
export RTEDEDE_MODEL_PATH=yolov8s.pt
export RTEDEDE_DETECTION_CONFIDENCE_THRESHOLD=0.6
export RTEDEDE_PREPROCESSING_TARGET_SIZE="[320, 320]"
```

---

## Testing Strategy

### Test Coverage

**Current Coverage:** 42% (395/681 lines)

**Coverage by Module:**
- `src/preprocessing/image_processor.py`: 98% ✅
- `src/utils/video_utils.py`: 83% ✅
- `src/config/config_manager.py`: 18%
- `src/models/yolo_detector.py`: 13%

### Test Organization

**Unit Tests (55 tests, 82% pass rate):**
- `test_image_processor.py` - Image preprocessing (29 tests)
- `test_video_utils.py` - Video utilities (26 tests)

**Integration Tests (12 tests, need mock fixes):**
- `test_video_processing_integration.py` - End-to-end pipeline

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_image_processor.py::TestImageProcessor::test_preprocess_normalization -v

# By marker
pytest -m unit -v          # Unit tests only
pytest -m integration -v   # Integration tests only
pytest -m "not slow" -v    # Skip slow tests
```

---

## Development Guidelines

### Code Style

- **PEP 8** compliance (enforced by pytest-black)
- Type hints for function signatures
- Docstrings for all public classes and methods

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `ImageProcessor`)
- **Functions/Methods:** `snake_case` (e.g., `preprocess_image`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_DETECTIONS`)
- **Private methods:** Leading underscore (e.g., `_internal_method`)

### Error Handling

**Custom Exceptions:**
- Defined in `src/core/errors.py`
- Use specific exceptions for different error scenarios
- Include helpful error messages

### Adding New Features

1. **Create feature branch:** `git checkout -b feature/your-feature`
2. **Write tests first:** Add tests to `tests/unit/`
3. **Implement feature:** Add code to `src/`
4. **Run tests:** `pytest tests/ -v`
5. **Check coverage:** `pytest --cov=src`
6. **Update documentation:** Add docstrings and examples
7. **Submit PR:** Describe changes and test results

---

## Performance Optimization

### Edge Device Considerations

**Quantization:**
- Convert `float32` → `int8` for 4x memory reduction
- Trade-off: Slight accuracy decrease

**Resolution Reduction:**
- Downscale input images for faster inference
- Example: 1920x1080 → 960x540 (0.5x scale)

**Memory Layout:**
- Use `np.ascontiguousarray()` for cache efficiency
- Avoid strided arrays

**Batch Processing:**
- Process multiple images in single batch
- Better GPU utilization

---

## Deployment

### Requirements

```bash
pip install -r requirements.txt
```

### Running Detection

**Single Image:**

```python
from src.models.yolo_detector import YOLODetector
import cv2

detector = YOLODetector(config='config.yaml')
detector.load_model()

image = cv2.imread('image.jpg')
detections = detector.detect(image)

for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.2f}")
```

**Video Processing:**

```python
detector.detect_video(
    video_path='input.mp4',
    output_path='output.mp4'
)
```

---

## Troubleshooting

### Common Issues

**Issue:** `ImportError: No module named 'ultralytics'`
**Solution:** `pip install ultralytics`

**Issue:** Model file not found
**Solution:** Check `model.path` in config.yaml, provide absolute path

**Issue:** Low FPS on video processing
**Solution:** Reduce `target_size`, enable quantization

**Issue:** Out of memory errors
**Solution:** Reduce batch size, lower target resolution

---

## Related Documentation

- **Automation Summary:** `_bmad-output/automation-summary.md` - Test automation details
- **Traceability Matrix:** `_bmad-output/traceability-matrix.md` - Requirements coverage
- **Test Review:** `_bmad-output/test-review.md` - Test quality assessment
- **Planning Artifacts:** `_bmad-output/planning-artifacts/` - PRD, architecture, epics

---

## Future Enhancements

**Short-term:**
- Fix integration test mocks (12 tests failing)
- Add YOLODetector edge case tests
- Expand ConfigManager test coverage

**Medium-term:**
- Add support for YOLO model variants (YOLOv5, YOLOv9)
- Implement ONNX export for deployment
- Add multi-threading for video processing

**Long-term:**
- GPU acceleration support
- Real-time streaming API
- Mobile deployment (TFLite, CoreML)

---

**Documentation Version:** 1.0
**Last Updated:** 2026-01-03
**Maintained By:** Project Team

<!-- Powered by BMAD-CORE™ -->
