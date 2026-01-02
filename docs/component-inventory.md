# Component Inventory

**Project:** realtime-edge-detection
**Generated:** 2026-01-02

## Overview

This document catalogs all software components in the realtime-edge-detection project.

## Core Components

### Detection Layer

#### YOLODetector

**Location:** `src/models/yolo_detector.py`
**Type:** Class
**Purpose:** Core object detection engine
**Dependencies:** ultralytics, OpenCV, NumPy

**Responsibilities:**

- Load and initialize YOLO v8 models
- Run inference on images
- Process video files
- Visualize detection results

**Key Methods:**

- `load_model()` - Initialize YOLO model
- `detect(image)` - Single image inference
- `detect_video(video_path, output_path)` - Video processing
- `draw_detections(frame, detections)` - Visualization

---

### Preprocessing Layer

#### ImageProcessor

**Location:** `src/preprocessing/image_processor.py`
**Type:** Class
**Purpose:** Image preprocessing for model input
**Dependencies:** OpenCV, NumPy

**Responsibilities:**

- Convert BGR to RGB
- Resize with letterbox padding
- Normalize images
- Batch processing

**Key Methods:**

- `preprocess(image)` - Standard preprocessing
- `resize(image, target_size)` - Aspect-ratio preserving resize
- `letterbox(image)` - YOLO-style padding
- `batch_preprocess(images)` - Batch processing

#### ImageAugmentor

**Location:** `src/preprocessing/image_processor.py`
**Type:** Class
**Purpose:** Training data augmentation
**Dependencies:** OpenCV, NumPy

**Responsibilities:**

- Horizontal flip
- Brightness/contrast adjustment
- Saturation adjustment
- Random crop

**Key Methods:**

- `augment(image, bboxes)` - Apply random augmentations
- `horizontal_flip(image, bboxes)` - Flip with bbox adjustment
- `adjust_brightness/contrast/saturation()` - Color adjustments

#### EdgeOptimizer

**Location:** `src/preprocessing/image_processor.py`
**Type:** Class
**Purpose:** Edge device optimizations
**Dependencies:** NumPy

**Responsibilities:**

- INT8 quantization
- Memory layout optimization
- Resolution reduction

**Key Methods:**

- `optimize_for_inference(image, quantize)` - Optimize for edge
- `_quantize_int8(image)` - Quantize to int8
- `reduce_resolution(image, scale)` - Lower resolution

---

### Video Utilities

#### VideoCapture

**Location:** `src/utils/video_utils.py`
**Type:** Class
**Purpose:** Enhanced video capture with buffering
**Dependencies:** OpenCV, threading, queue

**Responsibilities:**

- Multi-threaded frame capture
- Frame buffering
- FPS limiting

**Key Methods:**

- `start()` - Start capture thread
- `read()` - Read next frame
- `stop()` - Release resources
- `get_fps()` - Calculate actual FPS

**Features:**

- Background thread for non-blocking capture
- Configurable buffer size
- Frame dropping for low-latency

#### VideoWriter

**Location:** `src/utils/video_utils.py`
**Type:** Class
**Purpose:** Video output with codec support
**Dependencies:** OpenCV

**Responsibilities:**

- Write video files
- Multiple codec support
- Auto-sizing

**Key Methods:**

- `start(frame_size)` - Initialize writer
- `write(frame)` - Write frame
- `stop()` - Release resources

**Features:**

- Context manager support
- Auto-sizing from first frame

#### FrameProcessor

**Location:** `src/utils/video_utils.py`
**Type:** Class
**Purpose:** Video processing pipeline
**Dependencies:** VideoCapture, VideoWriter, OpenCV

**Responsibilities:**

- Detection loop
- FPS calculation
- Annotation/drawing
- Display management

**Key Methods:**

- `process_video(source, max_frames)` - Process video
- `_draw_detections(frame, detections, fps)` - Visualize results

**Features:**

- Real-time display
- Video output
- FPS statistics

---

## CLI Interface

#### run.py

**Location:** `run.py` (root)
**Type:** Script
**Purpose:** Main CLI entry point
**Dependencies:** argparse, YOLODetector, ImageProcessor

**Commands:**

- `detect` - Object detection in images
- `webcam` - Real-time webcam detection
- `video` - Video file processing
- `benchmark` - Performance benchmarking
- `preprocess` - Test preprocessing

**Features:**

- Argument parsing
- Progress indicators
- Error handling
- Emoji-enhanced output

---

## Component Relationships

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

## Design Patterns

1. **Strategy Pattern**: ImageProcessor supports multiple strategies
2. **Context Managers**: VideoCapture/VideoWriter resource management
3. **Factory Pattern**: YOLODetector model creation
4. **Facade Pattern**: CLI simplifies complex pipeline

## Reusability

**Reusable Components:**

- `YOLODetector` - Can be imported as library
- `ImageProcessor` - Generic preprocessing
- `VideoCapture` - Generic video I/O
- `VideoWriter` - Generic video output

**Customization Points:**

- Model selection (YOLO v8n, v8s, v8m, etc.)
- Preprocessing parameters (size, normalization)
- Video codec selection
- FPS targets

## Component Metrics

| Component | Lines of Code | Complexity | Dependencies |
|-----------|---------------|------------|--------------|
| YOLODetector | ~150 | Medium | 3 external |
| ImageProcessor | ~280 | High | 2 external |
| VideoCapture | ~130 | Medium | 2 external |
| VideoWriter | ~80 | Low | 1 external |
| FrameProcessor | ~150 | Medium | 3 external |
| run.py | ~150 | Low | 3 external |

**Total:** ~940 lines of core code (excluding tests and examples)
