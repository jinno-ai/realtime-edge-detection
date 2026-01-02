# Project Overview

**Project:** realtime-edge-detection
**Type:** CLI Tool / Python Library
**Repository:** Monolith
**Language:** Python

## Quick Reference

### Tech Stack

- **Primary:** Python 3.x
- **Framework:** Ultralytics YOLO v8
- **Backend:** PyTorch 2.1.0
- **Computer Vision:** OpenCV 4.8.1.78

### Entry Point

- **CLI:** `python run.py detect image.jpg`
- **Library:** `from src.models.yolo_detector import YOLODetector`

### Architecture Type

**Layered Architecture** with modular components:

- Detection Layer (YOLODetector)
- Preprocessing Layer (ImageProcessor)
- Video Utils Layer (VideoCapture, VideoWriter)

## Executive Summary

Real-time Edge Detection is a high-performance object detection toolkit optimized for edge devices. It provides real-time object detection capabilities using YOLO v8, with specific optimizations for resource-constrained hardware.

**Key Capabilities:**

- ⚡ 30+ FPS detection on edge devices
- 🎯 State-of-the-art YOLO v8 accuracy
- 🔧 Edge-specific optimizations (quantization, resolution scaling)
- 📹 Video processing pipeline
- 🖼️ Image preprocessing and augmentation
- 🎮 Simple CLI interface

**Target Users:**

- Computer vision developers
- Edge AI engineers
- Researchers
- IoT/embedded systems developers

## Repository Structure

This is a **monolithic repository** containing:

- Source library in `src/`
- CLI entry point at `run.py`
- Tests in `tests/`
- Examples in `examples/`
- Build scripts in `scripts/`

## Purpose

Provide a fast, accurate, and easy-to-use object detection solution that:

1. Runs efficiently on edge devices (CPU, ARM, GPU)
2. Offers both CLI tool and Python library interfaces
3. Supports real-time video processing
4. Includes comprehensive preprocessing pipeline

## Generated Documentation

### Core Documentation

- [Architecture](./architecture.md) - Detailed architecture documentation
- [Source Tree Analysis](./source-tree-analysis.md) - Annotated directory structure

### Existing Project Documentation

- [README](../README.md) - Quick start and usage guide
- [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) - Development phases (1-5)
- [Planning Artifacts](../_bmad-output/planning-artifacts/) - PRD, Architecture, Analysis
- [Epics and Stories](../_bmad-output/planning-artifacts/epics.md) - User stories (27 stories, 4 epics)

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/jinno-ai/realtime-edge-detection.git
cd realtime-edge-detection

# Install dependencies
pip install -r requirements.txt
```

### Quick Start

**CLI Usage:**

```bash
# Detect objects in image
python run.py detect image.jpg

# Real-time webcam detection
python run.py webcam

# Process video file
python run.py video input.mp4 --output output.mp4
```

**Python API:**

```python
from src.models.yolo_detector import YOLODetector
import cv2

# Initialize detector
detector = YOLODetector("yolov8n.pt", conf_threshold=0.5)
detector.load_model()

# Detect objects
image = cv2.imread("image.jpg")
detections = detector.detect(image)

# Display results
for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.3f}")
```

## Development Status

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

## Performance Benchmarks

- **Inference Latency:** < 30ms on CPU (640x640)
- **Throughput:** 30+ FPS on CPU
- **Model Size:** 6MB (YOLOv8n)
- **Accuracy:** mAP 37.3 on COCO val2017

## Hardware Support

- ✅ CPU (x86_64, ARM64)
- ✅ GPU (CUDA, MPS)
- ✅ Edge TPU (planned)
- ✅ Neural Engine (planned)

## License

MIT License - See [LICENSE](../LICENSE)

## Contributing

Contributions welcome! Please read the existing documentation and consider the planned enhancements in the Implementation Roadmap.
