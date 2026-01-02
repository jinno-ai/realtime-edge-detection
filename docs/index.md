# Real-time Edge Detection - Project Index

**Project:** realtime-edge-detection
**Type:** Monolith CLI Tool / Python Library
**Language:** Python 3.x
**Status:** Brownfield - Existing Codebase
**Last Updated:** 2026-01-02

---

## Quick Navigation

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Entry Points](#entry-points)
- [Core Components](#core-components)
- [Development Quick Start](#development-quick-start)
- [Architecture](#architecture)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation Links](#documentation-links)

---

## Project Overview

Real-time Edge Detection is a high-performance object detection toolkit optimized for edge devices. It provides real-time object detection using YOLO v8 with specific optimizations for resource-constrained hardware.

**Key Capabilities:**
- ⚡ 30+ FPS detection on edge devices
- 🎯 State-of-the-art YOLO v8 accuracy (mAP 37.3 on COCO)
- 🔧 Edge-specific optimizations (quantization, resolution scaling)
- 📹 Video processing pipeline with multi-threaded capture
- 🖼️ Image preprocessing and augmentation
- 🎮 Simple CLI interface + Python library API

**Target Users:**
- Computer vision developers
- Edge AI engineers
- Researchers
- IoT/embedded systems developers

**Repository Type:** Monolith (single codebase, CLI tool/library)

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.x | Primary language |
| **Deep Learning** | PyTorch | 2.1.0 | Model backend |
| **Object Detection** | Ultralytics YOLO | 8.0.230 | Detection engine |
| **Computer Vision** | OpenCV | 4.8.1.78 | Image/video I/O |
| **Numerical Computing** | NumPy | 1.24.3 | Array operations |
| **Image Processing** | Pillow | 10.1.0 | Image manipulation |
| **Configuration** | PyYAML | 6.0.1 | Config files |
| **Progress Bars** | tqdm | 4.66.1 | User feedback |

---

## Entry Points

### Primary Entry Point: CLI Tool

**File:** `run.py` (root directory)

**Basic Usage:**
```bash
# Detect objects in image
python run.py detect image.jpg

# Real-time webcam detection
python run.py webcam

# Process video file
python run.py video input.mp4 --output output.mp4

# Benchmark performance
python run.py benchmark --iterations 100

# Test preprocessing
python run.py preprocess image.jpg
```

**CLI Commands:**
- `detect` - Object detection in images
- `webcam` - Real-time webcam detection
- `video` - Video file processing
- `benchmark` - Performance benchmarking
- `preprocess` - Test preprocessing pipeline

### Library Entry Point

**Import as:** `from src.models.yolo_detector import YOLODetector`

**Basic Library Usage:**
```python
from src.models.yolo_detector import YOLODetector
import cv2

# Initialize detector
detector = YOLODetector("yolov8n.pt", conf_threshold=0.5)
detector.load_model()

# Detect objects
image = cv2.imread("image.jpg")
detections = detector.detect(image)

# Process results
for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.3f}")
```

---

## Core Components

### 1. Detection Layer

**YOLODetector** (`src/models/yolo_detector.py`)
- **Purpose:** Core object detection engine
- **Dependencies:** ultralytics, OpenCV, NumPy
- **Key Methods:**
  - `load_model()` - Initialize YOLO v8 model
  - `detect(image)` - Single image inference
  - `detect_video(video_path, output_path)` - Video processing
  - `draw_detections(frame, detections)` - Visualization

### 2. Preprocessing Layer

**ImageProcessor** (`src/preprocessing/image_processor.py`)
- **Purpose:** Image preprocessing for model input
- **Dependencies:** OpenCV, NumPy
- **Key Methods:**
  - `preprocess(image)` - Standard preprocessing (BGR→RGB, resize, normalize)
  - `resize(image, target_size)` - Aspect-ratio preserving resize
  - `letterbox(image)` - YOLO-style padding
  - `batch_preprocess(images)` - Batch processing

**ImageAugmentor** (`src/preprocessing/image_processor.py`)
- **Purpose:** Training data augmentation
- **Features:** Horizontal flip, brightness/contrast/saturation adjustment, random crop

**EdgeOptimizer** (`src/preprocessing/image_processor.py`)
- **Purpose:** Edge device optimizations
- **Features:** INT8 quantization, memory layout optimization, resolution reduction

### 3. Video Utilities

**VideoCapture** (`src/utils/video_utils.py`)
- **Purpose:** Enhanced video capture with buffering
- **Dependencies:** OpenCV, threading, queue
- **Features:** Multi-threaded frame capture, frame buffering, FPS limiting

**VideoWriter** (`src/utils/video_utils.py`)
- **Purpose:** Video output with codec support
- **Features:** Multiple codec support, auto-sizing, context manager support

**FrameProcessor** (`src/utils/video_utils.py`)
- **Purpose:** Video processing pipeline
- **Features:** Detection loop, FPS calculation, annotation/drawing, display management

---

## Development Quick Start

### Prerequisites

- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended)
- 500MB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/jinno-ai/realtime-edge-detection.git
cd realtime-edge-detection

# (Optional) Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import torch; import cv2; import ultralytics; print('✅ All dependencies installed')"
```

### Quick Verification

```bash
# Run basic detection test
python run.py detect <path_to_test_image>

# Run benchmark
python run.py benchmark --iterations 10
```

---

## Architecture

### Architecture Pattern

**Modular Object-Oriented Design (Layered Architecture)**

```
┌─────────────────────────────────────────┐
│         CLI Interface (run.py)          │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Detection Layer                  │
│  (YOLODetector - models/yolo_detector.py)│
└──────────────────┬──────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
┌─────▼──────┐          ┌──────▼────────┐
│Preprocessing│          │  Video Utils   │
│(ImageProcessor)     │ (VideoCapture, │
│  - preprocess       │  VideoWriter,   │
│  - augment          │  FrameProcessor)│
│  - optimize         │                │
└────────────┘          └───────────────┘
```

### Design Patterns

1. **Strategy Pattern**: ImageProcessor supports multiple preprocessing strategies
2. **Context Managers**: Resource management for video I/O
3. **Factory Pattern**: YOLODetector abstracts model creation
4. **Facade Pattern**: Simple CLI hiding complex detection pipeline

### Component Relationships

```
run.py (CLI)
    ↓
YOLODetector (Detection)
    ↓
ImageProcessor (Preprocessing) ──────┐
    ↓                                │
VideoCapture (Input)              EdgeOptimizer
    ↓                                │
FrameProcessor ──────────────────────┘
    ↓
VideoWriter (Output)
```

---

## Testing

### Test Structure

Tests located in `tests/` directory:
- Unit tests for individual components
- Integration tests for workflows
- Performance tests for benchmarks

### Running Tests

```bash
# Using pytest (recommended)
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test files
pytest tests/test_yolo_detector.py
pytest tests/test_image_processor.py
pytest tests/test_video_utils.py
```

### Test Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests: Core workflows
- Performance tests: Key benchmarks

---

## Deployment

### Hardware Requirements

**Minimum:**
- 2GB RAM, CPU x86_64/ARM64

**Recommended:**
- 4GB RAM, GPU with CUDA support

**Optimal:**
- 8GB RAM, NVIDIA GPU (Jetson Nano/Xavier)

### Target Platforms

- ✅ Linux x86_64
- ✅ Linux ARM64 (Raspberry Pi)
- ✅ NVIDIA Jetson (CUDA support)
- ✅ Windows (experimental)
- ✅ macOS (experimental)

### Deployment as Service (systemd example)

```ini
# /etc/systemd/system/edge-detection.service
[Unit]
Description=Edge Detection Service
After=network.target

[Service]
Type=simple
User=edge
WorkingDirectory=/opt/realtime-edge-detection
ExecStart=/usr/bin/python3 /opt/realtime-edge-detection/run.py webcam
Restart=always

[Install]
WantedBy=multi-user.target
```

### Performance Benchmarks

- **Inference Latency:** < 30ms (640x640 image on CPU)
- **Throughput:** 30+ FPS on CPU, higher on GPU
- **Model Size:** 6MB (YOLOv8n)
- **Memory Usage:** < 500MB (excluding model)

### Optimizations

- **Letterbox resize**: Efficient padding
- **INT8 quantization**: Reduced precision for edge devices
- **Buffered video capture**: Multi-threaded frame reading
- **Zero-copy operations**: NumPy array views

---

## Documentation Links

### Core Documentation

- [Project Overview](./project-overview.md) - Executive summary and quick reference
- [Architecture Documentation](./architecture.md) - Detailed architecture and design patterns
- [Source Tree Analysis](./source-tree-analysis.md) - Annotated directory structure
- [Component Inventory](./component-inventory.md) - Catalog of all components
- [Development Guide](./development-guide.md) - Comprehensive development setup and workflows

### Existing Project Documentation

- [README](../README.md) - Quick start and usage guide
- [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) - Development phases (1-5)
- [Planning Artifacts](../_bmad-output/planning-artifacts/) - PRD, Architecture Analysis
- [Epics and Stories](../_bmad-output/planning-artifacts/epics.md) - User stories (27 stories, 4 epics)

### Project Status

**Current Phase:** Brownfield - Existing codebase with comprehensive planning

**Completed:**
- ✅ Core detection engine (YOLO v8 integration)
- ✅ Image preprocessing pipeline
- ✅ Video processing utilities
- ✅ CLI interface
- ✅ PRD, Architecture, Epics documentation

**Next Steps (from Epics):**
- Epic 1: Project Setup & Basic Detection (configuration management)
- Epic 2: Model Flexibility & Optimization (abstraction, quantization)
- Epic 3: Production Readiness (logging, monitoring, testing)
- Epic 4: Advanced Features (video streaming, tracking, deployment)

---

## Known Limitations

1. **Single-threaded inference**: No model parallelism
2. **No batch processing for images**: Only video batch support
3. **Limited model support**: Only YOLO v8/v10
4. **No ONNX export yet**: Planned for future
5. **No configuration file support**: CLI args only

---

## Future Enhancements (from PRD)

### Epic 1: Project Setup & Basic Detection
- YAML configuration management
- Environment variable overrides
- Profile-based configs

### Epic 2: Model Flexibility & Optimization
- Abstract detector interface
- Multiple model support
- ONNX export
- TensorRT integration
- Device auto-detection

### Epic 3: Production Readiness & Monitoring
- Structured logging
- Error handling framework
- Test suite expansion
- Metrics collection

### Epic 4: Advanced Features & Integration
- Video streaming (RTSP, WebRTC)
- Multi-object tracking
- Docker/K8s deployment
- Edge TPU support

---

## Quick Reference for AI Agents

### Key Commands

```bash
# Run detection
python run.py detect image.jpg --show --output result.jpg

# Run webcam
python run.py webcam --model yolov8n.pt --confidence 0.5

# Benchmark
python run.py benchmark --iterations 100
```

### Key Files

- `run.py` - CLI entry point
- `src/models/yolo_detector.py` - Detection engine
- `src/preprocessing/image_processor.py` - Preprocessing pipeline
- `src/utils/video_utils.py` - Video I/O utilities
- `requirements.txt` - Dependencies

### Important Classes

- `YOLODetector` - Main detection class
- `ImageProcessor` - Image preprocessing
- `ImageAugmentor` - Data augmentation
- `EdgeOptimizer` - Edge optimizations
- `VideoCapture` - Threaded video capture
- `VideoWriter` - Video output
- `FrameProcessor` - Video processing pipeline

### Common Tasks

**Add new model support:**
1. Update `YOLODetector` class
2. Add model loading logic
3. Update CLI arguments
4. Add tests

**Add new preprocessing:**
1. Update `ImageProcessor` class
2. Add method with proper typing
3. Add tests

**Debug performance:**
```bash
python -m cProfile -o profile.stats run.py detect image.jpg
```

---

**License:** MIT
**Repository:** https://github.com/jinno-ai/realtime-edge-detection
