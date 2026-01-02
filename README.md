# Real-time Edge Detection

Low-latency object detection optimized for edge devices. Uses YOLO v8 for fast, accurate detection on resource-constrained hardware.

## Features

- ⚡ **Real-time Detection**: 30+ FPS on edge devices
- 🎯 **High Accuracy**: YOLO v8 state-of-the-art model
- 🔧 **Optimization**: Edge-specific optimizations (quantization, resolution reduction)
- 📹 **Video Processing**: Batch video processing support
- 🖼️ **Image Preprocessing**: Augmentation and letterbox support
- 🎮 **Easy CLI**: Simple command-line interface

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### CLI Usage

```bash
# Detect objects in image
python run.py detect image.jpg --show

# Real-time webcam detection
python run.py webcam

# Process video file
python run.py video input.mp4 --output output.mp4

# Benchmark performance
python run.py benchmark --iterations 100

# Test preprocessing
python run.py preprocess image.jpg
```

### Python API

```python
from src.models.yolo_detector import YOLODetector

# Initialize
detector = YOLODetector("yolov8n.pt", conf_threshold=0.5)
detector.load_model()

# Detect
image = cv2.imread("image.jpg")
detections = detector.detect(image)

for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.3f}")
```

## Performance

- **Latency**: < 30ms per inference (640x640)
- **Throughput**: 30+ FPS on CPU
- **Model Size**: 6MB (YOLOv8n)
- **Accuracy**: mAP 37.3 on COCO

## Hardware Support

- ✅ CPU (x86, ARM)
- ✅ GPU (CUDA, MPS)
- ✅ Edge TPU
- ✅ Neural Engine

## License

MIT
