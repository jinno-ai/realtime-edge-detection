# Development Guide

**Project:** realtime-edge-detection
**Type:** CLI Tool / Python Library
**Generated:** 2026-01-02

## Overview

This guide provides comprehensive instructions for developing, testing, and deploying the realtime-edge-detection project.

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.8 or higher
- 2GB RAM
- CPU (x86_64 or ARM64)
- 500MB disk space

**Recommended:**
- Python 3.10
- 4GB RAM
- GPU with CUDA support (NVIDIA)
- 1GB disk space

### Operating System Support

- ✅ Linux (x86_64, ARM64) - Primary platform
- ✅ Windows (experimental)
- ✅ macOS (experimental)

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/jinno-ai/realtime-edge-detection.git
cd realtime-edge-detection
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import torch; import cv2; import ultralytics; print('✅ All dependencies installed')"
```

### 4. Download Model (Optional)

The first run will automatically download YOLOv8n model. To download manually:

```bash
# Using Python
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Or use wget
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### 5. Verify Installation

```bash
# Run basic detection test
python run.py detect <path_to_test_image>

# Run benchmark
python run.py benchmark --iterations 10
```

## Local Development

### Project Structure

```
realtime-edge-detection/
├── src/                    # Source library
│   ├── models/            # Detection algorithms
│   ├── preprocessing/     # Image processing
│   └── utils/             # Video utilities
├── tests/                 # Test suite
├── examples/              # Usage examples
├── scripts/               # Build/deployment scripts
└── run.py                 # CLI entry point
```

### Running the CLI Tool

**Image Detection:**
```bash
# Basic detection
python run.py detect image.jpg

# With visualization
python run.py detect image.jpg --show

# Save output
python run.py detect image.jpg --output result.jpg

# Custom confidence threshold
python run.py detect image.jpg --confidence 0.7

# Use different model
python run.py detect image.jpg --model yolov8s.pt
```

**Real-time Webcam Detection:**
```bash
# Default webcam (index 0)
python run.py webcam

# Specify camera index
python run.py webcam --camera 1

# Custom model and threshold
python run.py webcam --model yolov8n.pt --confidence 0.6
```

**Video Processing:**
```bash
# Process video file
python run.py video input.mp4

# Specify output path
python run.py video input.mp4 --output result.mp4
```

**Performance Benchmarking:**
```bash
# Run benchmark (100 iterations)
python run.py benchmark

# Custom iterations
python run.py benchmark --iterations 1000

# Test different models
python run.py benchmark --model yolov8s.pt
```

**Test Preprocessing:**
```bash
# Test letterbox and preprocessing
python run.py preprocess image.jpg
```

### Using as Python Library

```python
# Basic usage
from src.models.yolo_detector import YOLODetector
import cv2

# Initialize detector
detector = YOLODetector("yolov8n.pt", conf_threshold=0.5)
detector.load_model()

# Load image
image = cv2.imread("image.jpg")

# Detect objects
detections = detector.detect(image)

# Process results
for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.3f} at {det['bbox']}")

# Visualize
result = detector.draw_detections(image, detections)
cv2.imwrite("output.jpg", result)
```

**Video Processing with Library:**
```python
from src.models.yolo_detector import YOLODetector

detector = YOLODetector("yolov8n.pt")
detector.load_model()

# Process entire video
detector.detect_video("input.mp4", "output.mp4")
```

**Using ImageProcessor:**
```python
from src.preprocessing.image_processor import ImageProcessor

processor = ImageProcessor(target_size=(640, 640))

# Preprocess single image
processed = processor.preprocess(image)

# Letterbox resize
padded, scale, padding = processor.letterbox(image)

# Batch processing
batch = processor.batch_preprocess([image1, image2, image3])
```

**Using VideoCapture:**
```python
from src.utils.video_utils import VideoCapture

# Threaded video capture
with VideoCapture(0) as cap:
    while True:
        frame = cap.read()
        if frame is None:
            break
        # Process frame...
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
```

## Build Process

### No Compilation Required

This is a pure Python project - no build step needed. The code runs directly from source.

### Creating Distribution

**Option 1: Source Distribution (sdist)**
```bash
# Setup setup.py if not present
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="realtime-edge-detection",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'opencv-python==4.8.1.78',
        'numpy==1.24.3',
        'ultralytics==8.0.230',
        'torch==2.1.0',
        'torchvision==0.16.0',
        'pyyaml==6.0.1',
    ],
    python_requires='>=3.8',
)
EOF

# Build source distribution
python setup.py sdist
```

**Option 2: Wheel Distribution**
```bash
pip install wheel
python setup.py bdist_wheel
```

**Option 3: PyPI Publishing**
```bash
# Install twine
pip install twine

# Upload to PyPI (test first)
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
```

### Docker Support (Future)

Planned for Epic 4 - Advanced Features:
```dockerfile
# Future Dockerfile example
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run.py"]
```

## Testing

### Test Structure

Tests are located in `tests/` directory:
- Unit tests for individual components
- Integration tests for workflows
- Performance tests for benchmarks

### Running Tests

**All Tests:**
```bash
# Using pytest (recommended)
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Verbose output
pytest tests/ -v
```

**Specific Test Files:**
```bash
# Test detection
pytest tests/test_yolo_detector.py

# Test preprocessing
pytest tests/test_image_processor.py

# Test video utilities
pytest tests/test_video_utils.py
```

**Specific Test Cases:**
```bash
# Run by keyword
pytest tests/ -k "test_load_model"

# Run by marker
pytest tests/ -m "slow"
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
import numpy as np
from src.models.yolo_detector import YOLODetector

def test_detector_initialization():
    detector = YOLODetector("yolov8n.pt")
    assert detector.model_path == "yolov8n.pt"
    assert detector.conf_threshold == 0.5

def test_model_loading():
    detector = YOLODetector("yolov8n.pt")
    detector.load_model()
    assert detector.model is not None

def test_detection():
    detector = YOLODetector("yolov8n.pt")
    detector.load_model()
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    detections = detector.detect(test_image)
    assert isinstance(detections, list)
```

**Integration Test Example:**
```python
def test_cli_detect_command():
    from click.testing import CliRunner
    from run import main

    runner = CliRunner()
    result = runner.invoke(main, ['detect', 'test_image.jpg'])
    assert result.exit_code == 0
    assert 'Detecting objects' in result.output
```

### Test Coverage

Aim for:
- Unit tests: 80%+ coverage
- Integration tests: Core workflows
- Performance tests: Key benchmarks

## Common Development Tasks

### Adding New Model Support

1. Update `YOLODetector` class in `src/models/yolo_detector.py`
2. Add model loading logic
3. Update CLI arguments in `run.py`
4. Add tests in `tests/test_yolo_detector.py`

**Example:**
```python
# In yolo_detector.py
def load_model(self, model_type="yolov8"):
    if model_type == "yolov8":
        from ultralytics import YOLO
        self.model = YOLO(self.model_path)
    elif model_type == "yolov10":
        # Add YOLOv10 support
        pass
```

### Adding New Preprocessing Methods

1. Update `ImageProcessor` in `src/preprocessing/image_processor.py`
2. Add method with proper typing
3. Add tests
4. Update CLI if needed

**Example:**
```python
# In image_processor.py
def normalize_custom(self, image: np.ndarray) -> np.ndarray:
    """Custom normalization method"""
    return image.astype(np.float32) / 255.0
```

### Adding New CLI Commands

1. Create command function in `run.py`
2. Add subparser in `main()`
3. Add arguments
4. Add help text

**Example:**
```python
# In run.py
def new_command(args):
    """New command implementation"""
    print("Executing new command...")

# In main()
new_parser = subparsers.add_parser('newcmd', help='New command')
new_parser.add_argument('--param', default='value', help='Parameter')
```

### Performance Optimization

**Profile Code:**
```bash
# Use cProfile
python -m cProfile -o profile.stats run.py detect image.jpg

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

**Benchmark Changes:**
```bash
# Before optimization
python run.py benchmark --iterations 1000 > before.txt

# After optimization
python run.py benchmark --iterations 1000 > after.txt

# Compare
diff before.txt after.txt
```

### Debugging

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Debug with pdb:**
```bash
python -m pdb run.py detect image.jpg
```

**VS Code Debug Configuration:**
```json
{
    "name": "Python: CLI",
    "type": "python",
    "request": "launch",
    "program": "run.py",
    "args": ["detect", "image.jpg", "--show"],
    "console": "integratedTerminal"
}
```

### Code Style

**Formatting with Black:**
```bash
pip install black
black src/ tests/ run.py
```

**Linting with Pylint:**
```bash
pip install pylint
pylint src/
```

**Type Checking with mypy:**
```bash
pip install mypy
mypy src/
```

## Troubleshooting

### Common Issues

**Issue: Model not found**
```bash
# Solution: Download model manually
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

**Issue: CUDA out of memory**
```bash
# Solution: Use smaller model or CPU
python run.py detect image.jpg --model yolov8n.pt
# Or force CPU
CUDA_VISIBLE_DEVICES="" python run.py detect image.jpg
```

**Issue: Webcam not opening**
```bash
# Solution: Check camera index
python -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).isOpened()])"
```

**Issue: Import errors**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Contributing

### Development Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit: `git commit -m "Add feature"`
4. Push to fork: `git push origin feature/my-feature`
5. Create pull request

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Follows code style
- [ ] Performance impact assessed

## Deployment

### Production Deployment

**Edge Device Deployment:**
```bash
# Install on target device
scp -r realtime-edge-detection user@edge-device:/opt/
ssh user@edge-device
cd /opt/realtime-edge-detection
pip install -r requirements.txt
python run.py webcam --camera 0
```

**Running as Service (systemd):**
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

```bash
# Enable and start
sudo systemctl enable edge-detection
sudo systemctl start edge-detection
sudo systemctl status edge-detection
```

### Performance Tuning

**CPU Optimization:**
- Use YOLOv8n (nano) model
- Enable OpenMP: `export OMP_NUM_THREADS=4`
- Reduce input resolution

**GPU Optimization:**
- Use CUDA-enabled PyTorch
- Enable TensorRT (Epic 2)
- Batch processing when possible

**ARM Optimization:**
- Compile with NEON support
- Use ARM-optimized PyTorch
- Enable INT8 quantization

## Next Steps

After setup:
1. Run `python run.py benchmark` to verify performance
2. Check out `examples/` directory for usage patterns
3. Review [architecture.md](./architecture.md) for design details
4. See [component-inventory.md](./component-inventory.md) for available components
5. Implement stories from [epics.md](../_bmad-output/planning-artifacts/epics.md)
