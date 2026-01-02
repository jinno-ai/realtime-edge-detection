# Source Tree Analysis

**Project:** realtime-edge-detection
**Type:** Monolith CLI Tool/Library
**Generated:** 2026-01-02

## Project Structure

```
realtime-edge-detection/
├── src/                          # Main source code directory
│   ├── models/                   # Object detection models
│   │   ├── __init__.py
│   │   └── yolo_detector.py     # YOLO v8 detector implementation
│   ├── preprocessing/            # Image preprocessing pipeline
│   │   ├── __init__.py
│   │   └── image_processor.py   # Image preprocessing and augmentation
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       └── video_utils.py       # Video capture and processing utilities
├── tests/                        # Test suite
├── examples/                     # Usage examples
├── scripts/                      # Build and deployment scripts
├── run.py                        # 🎯 Main CLI entry point
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── IMPLEMENTATION_ROADMAP.md    # Implementation phases (1-5)
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

## Critical Folders

### `src/` - Core Library

Contains the main detection library with modular architecture:

- **models/**: Detection algorithms (YOLO v8)
- **preprocessing/**: Image processing pipeline
- **utils/**: Video I/O and frame processing utilities

### `tests/` - Test Suite

Integration and unit tests for the detection pipeline

### `examples/` - Usage Examples

Sample code demonstrating how to use the library

## Entry Points

### Primary Entry Point

**`run.py`** - CLI tool entry point

```bash
python run.py detect image.jpg
python run.py webcam
python run.py video input.mp4
python run.py benchmark
```

### Library Entry Point

**`src/__init__.py`** - Package initialization
Import as: `from src.models import YOLODetector`

## Architecture Pattern

**Modular Object-Oriented Design**

- Class-based components (YOLODetector, ImageProcessor, VideoCapture, VideoWriter)
- Separation of concerns (detection, preprocessing, video I/O)
- Context managers for resource management
- Type hints throughout

## Key Design Patterns

1. **Strategy Pattern**: ImageProcessor supports multiple preprocessing strategies
2. **Context Managers**: VideoCapture and VideoWriter use context managers
3. **Factory Pattern**: YOLODetector abstracts model creation
4. **Singleton Pattern**: Single model instance per detector

## Integration Points

This is a monolithic library with no external part dependencies.

## Dependencies

**External:**

- ultralytics (YOLO v8)
- torch (PyTorch)
- opencv-python (OpenCV)
- numpy, pillow

**Internal:**

- No internal dependencies between modules (clean separation)
