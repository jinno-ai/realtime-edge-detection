# Architecture Documentation

**Project:** realtime-edge-detection
**Type:** CLI Tool / Python Library
**Generated:** 2026-01-02
**Status:** Brownfield - Existing Codebase

## Executive Summary

Real-time Edge Detection is a high-performance object detection toolkit optimized for edge devices. It provides:

- **Real-time detection**: 30+ FPS on edge hardware
- **YOLO v8 integration**: State-of-the-art accuracy
- **CLI tool**: Easy command-line interface
- **Python library**: Reusable API for integration
- **Edge optimization**: Quantization, resolution scaling, efficient preprocessing

**Target Users:** Computer vision developers, edge AI engineers, researchers

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

## Architecture Pattern

### Modular Object-Oriented Design

The codebase follows a **layered architecture** with clear separation of concerns:

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

### Key Design Patterns

1. **Strategy Pattern**: ImageProcessor supports multiple preprocessing strategies
   - Standard preprocessing
   - Letterbox resize (YOLO-style)
   - Edge optimization (quantization)
   - Batch preprocessing

2. **Context Managers**: Resource management for video I/O
   - `VideoCapture.__enter__/__exit__`
   - `VideoWriter.__enter__/__exit__`

3. **Factory Pattern**: YOLODetector abstracts model creation
   - Dynamic model loading
   - Version management
   - Configuration flexibility

4. **Facade Pattern**: Simple CLI hiding complex detection pipeline

## Component Overview

### 1. YOLODetector (`src/models/yolo_detector.py`)

**Responsibility**: Core object detection engine

**Key Methods**:

- `load_model()`: Initialize YOLO v8 model
- `detect(image)`: Run inference on single image
- `detect_video(video_path, output_path)`: Process video file
- `draw_detections(frame, detections)`: Visualize results

**Dependencies**: ultralytics, OpenCV, NumPy

### 2. ImageProcessor (`src/preprocessing/image_processor.py`)

**Responsibility**: Image preprocessing and augmentation

**Key Classes**:

- `ImageProcessor`: Standard preprocessing pipeline
  - BGR to RGB conversion
  - Resize with letterbox
  - Normalization
  - Batch processing

- `ImageAugmentor`: Training data augmentation
  - Horizontal flip
  - Brightness/contrast adjustment
  - Saturation adjustment
  - Random crop

- `EdgeOptimizer`: Edge device optimizations
  - INT8 quantization
  - Resolution reduction
  - Memory layout optimization

**Dependencies**: OpenCV, NumPy

### 3. Video Utils (`src/utils/video_utils.py`)

**Responsibility**: Video capture and processing

**Key Classes**:

- `VideoCapture`: Buffered video capture with threading
  - Background thread for frame capture
  - Frame queue for buffering
  - FPS limiting

- `VideoWriter`: Video output with codec support
  - Multiple codec options
  - Auto-sizing

- `FrameProcessor`: Video processing pipeline
  - Detection loop
  - FPS calculation
  - Annotation/drawing

**Dependencies**: OpenCV, threading, queue

## Source Tree

See [source-tree-analysis.md](./source-tree-analysis.md)

## Development Workflow

### Installation

```bash
# Clone repository
git clone https://github.com/jinno-ai/realtime-edge-detection.git
cd realtime-edge-detection

# Install dependencies
pip install -r requirements.txt
```

### Local Development

```bash
# Run detection on image
python run.py detect image.jpg

# Real-time webcam detection
python run.py webcam

# Process video
python run.py video input.mp4 --output output.mp4

# Benchmark performance
python run.py benchmark --iterations 100
```

### Testing

Test files located in `tests/` directory.

```bash
# Run all tests (when test runner is configured)
pytest tests/
```

### Building

No build step required - interpreted Python code.

## Deployment Architecture

### Current Deployment

- **Platform**: Standalone CLI tool
- **Deployment**: Direct Python execution
- **Containerization**: Not yet configured

### Target Platforms

- Linux x86_64
- Linux ARM64 (Raspberry Pi)
- NVIDIA Jetson (CUDA support)
- Windows (experimental)
- macOS (experimental)

### Hardware Requirements

- **Minimum**: 2GB RAM, CPU x86_64/ARM64
- **Recommended**: 4GB RAM, GPU with CUDA support
- **Optimal**: 8GB RAM, NVIDIA GPU (Jetson Nano/Xavier)

## Testing Strategy

### Test Types

1. **Unit Tests**: Individual component testing
   - Model loading
   - Preprocessing functions
   - Video utilities

2. **Integration Tests**: End-to-end workflows
   - CLI commands
   - Video processing pipeline
   - Detection accuracy

3. **Performance Tests**: Benchmarking
   - Inference latency
   - FPS measurement
   - Memory usage

### Test Coverage

Current test coverage status: **To be determined**

## Performance Characteristics

### Benchmarks

- **Inference Latency**: < 30ms (640x640 image on CPU)
- **Throughput**: 30+ FPS on CPU, higher on GPU
- **Model Size**: 6MB (YOLOv8n)
- **Memory Usage**: < 500MB (excluding model)

### Optimizations

- **Letterbox resize**: Efficient padding
- **INT8 quantization**: Reduced precision for edge devices
- **Buffered video capture**: Multi-threaded frame reading
- **Zero-copy operations**: NumPy array views

## Known Limitations

1. **Single-threaded inference**: No model parallelism
2. **No batch processing for images**: Only video batch support
3. **Limited model support**: Only YOLO v8/v10
4. **No ONNX export yet**: Planned for future
5. **No configuration file support**: CLI args only

## Future Architecture Considerations

Based on PRD and Architecture docs, planned enhancements:

1. **Configuration Management** (Epic 1)
   - YAML config files
   - Environment variable overrides
   - Profile-based configs

2. **Model Abstraction** (Epic 2)
   - Abstract detector interface
   - Multiple model support
   - ONNX export

3. **Hardware Optimization** (Epic 2)
   - Quantization pipeline
   - TensorRT integration
   - Device auto-detection

4. **Production Readiness** (Epic 3)
   - Structured logging
   - Error handling framework
   - Test suite expansion

5. **Advanced Features** (Epic 4)
   - Video streaming (RTSP, WebRTC)
   - Multi-object tracking
   - Docker/K8s deployment
