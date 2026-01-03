# Troubleshooting Guide

Common problems and solutions for the Real-time Edge Detection library.

## Table of Contents

- [Installation Issues](#installation-issues)
- [CUDA Errors](#cuda-errors)
- [Model Download Failures](#model-download-failures)
- [Low FPS Issues](#low-fps-issues)
- [Memory Issues](#memory-issues)
- [Device Compatibility Problems](#device-compatibility-problems)
- [Detection Accuracy Issues](#detection-accuracy-issues)
- [Configuration Problems](#configuration-problems)

---

## Installation Issues

### Error: Module not found

**Symptom:**
```python
ImportError: No module named 'src'
```

**Solution:**
1. Ensure you're in the project root directory
2. Install the package in development mode:
   ```bash
   pip install -e .
   ```
3. Or add the project root to PYTHONPATH:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/project"
   ```

---

### Error: Failed building wheel for dependencies

**Symptom:**
```
Failed building wheel for opencv-python
error: Microsoft Visual C++ 14.0 is required
```

**Solution:**
1. Install build tools:
   - **Windows**: Install Visual Studio Build Tools
   - **Linux**: `sudo apt-get install build-essential`
   - **macOS**: Install Xcode Command Line Tools

2. Install pre-built wheels:
   ```bash
   pip install opencv-python-headless
   ```

---

### Error: Version conflicts

**Symptom:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solution:**
1. Create a fresh virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Check for conflicts:
   ```bash
   pip check
   ```

---

## CUDA Errors

### Error: CUDA out of memory

**Symptom:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Solutions:**

1. **Use smaller model:**
   ```python
   detector = YOLODetector(model_path='yolov8n.pt')  # nano instead of large
   ```

2. **Reduce batch size:**
   ```python
   processor = BatchProcessor(batch_size=1)  # Process one at a time
   ```

3. **Clear GPU cache:**
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

4. **Use CPU fallback:**
   ```python
   device_manager = DeviceManager(device='cpu')  # Force CPU
   ```

5. **Reduce image resolution:**
   ```python
   # Resize images before detection
   image = cv2.resize(image, (640, 640))
   ```

---

### Error: CUDA not available

**Symptom:**
```
AssertionError: Torch not compiled with CUDA enabled
```

**Solutions:**

1. **Verify CUDA installation:**
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Install CUDA-enabled PyTorch:**
   ```bash
   # For CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

   # For CUDA 12.1
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Install NVIDIA drivers:**
   - Linux: `sudo apt-get install nvidia-driver-535`
   - Windows: Download from [NVIDIA website](https://www.nvidia.com/Download/index.aspx)

4. **Use CPU if CUDA unavailable:**
   ```python
   device_manager = DeviceManager(device='auto')  # Will fallback to CPU
   ```

---

### Error: CUDA driver version too old

**Symptom:**
```
RuntimeError: The detected CUDA version (11.7) mismatches the version that was used to compile PyTorch (11.8)
```

**Solution:**
1. Update NVIDIA drivers to latest version
2. Or install PyTorch with matching CUDA version:
   ```bash
   # Check your CUDA version
   nvcc --version

   # Install matching PyTorch version
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu117
   ```

---

## Model Download Failures

### Error: Model file not found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'yolov8n.pt'
```

**Solutions:**

1. **Download model manually:**
   ```bash
   # From Ultralytics
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

   # Or use Python
   from src.models.model_manager import ModelManager
   manager = ModelManager()
   manager.download_model('yolov8n.pt')
   ```

2. **Specify correct model path:**
   ```python
   detector = YOLODetector(model_path='./models/yolov8n.pt')
   ```

3. **Set MODEL_PATH environment variable:**
   ```bash
   export MODEL_PATH=/path/to/models
   ```

---

### Error: Download timeout

**Symptom:**
```
TimeoutError: Download timeout for yolov8n.pt
```

**Solutions:**

1. **Increase timeout:**
   ```python
   from src.models.model_manager import ModelManager
   manager = ModelManager(timeout=300)  # 5 minutes
   manager.download_model('yolov8n.pt')
   ```

2. **Download manually from browser:**
   - Visit: https://github.com/ultralytics/assets/releases
   - Download model file
   - Place in `models/` directory

3. **Use mirror or alternative source:**
   ```bash
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
   ```

---

### Error: Model file corrupted

**Symptom:**
```
EOFError: Ran out of input
```

**Solution:**
1. Delete corrupted model file:
   ```bash
   rm yolov8n.pt
   ```

2. Re-download model:
   ```python
   from src.models.model_manager import ModelManager
   manager = ModelManager()
   manager.download_model('yolov8n.pt', force=True)
   ```

3. Verify file integrity:
   ```python
   import os
   size = os.path.getsize('yolov8n.pt')
   print(f"Model size: {size / 1024 / 1024:.2f} MB")
   # yolov8n.pt should be ~6 MB
   ```

---

## Low FPS Issues

### Symptom: Detection is slow (<10 FPS)

**Solutions:**

1. **Use smaller model:**
   ```python
   # Fastest: yolov8n (nano)
   detector = YOLODetector(model_path='yolov8n.pt')

   # Balanced: yolov8s (small)
   detector = YOLODetector(model_path='yolov8s.pt')

   # Avoid: yolov8x (extra large) - too slow
   ```

2. **Use GPU acceleration:**
   ```python
   device_manager = DeviceManager(device='cuda')  # 10-50x faster
   ```

3. **Use ONNX Runtime:**
   ```python
   from src.models.onnx import ONNXDetector
   detector = ONNXDetector(model_path='yolov8n.onnx')  # 2-3x faster
   ```

4. **Optimize with quantization:**
   ```python
   from src.commands.quantize import quantize_model
   quantize_model('yolov8n.pt', 'yolov8n_int8.pt')  # 2-4x faster
   ```

5. **Reduce image resolution:**
   ```python
   # Resize before detection
   image = cv2.resize(image, (640, 480))  # Lower resolution
   ```

6. **Increase confidence threshold:**
   ```python
   detector = YOLODetector(
       model_path='yolov8n.pt',
       confidence_threshold=0.7  # Reduces post-processing
   )
   ```

7. **Disable visual output:**
   ```python
   # For batch processing, don't save visual output
   edge-detection detect image.jpg --output-format json  # Faster
   ```

---

## Memory Issues

### Error: Out of memory on CPU

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Process images sequentially:**
   ```python
   processor = BatchProcessor(batch_size=1)
   ```

2. **Reduce image resolution:**
   ```python
   image = cv2.resize(image, (640, 480))
   ```

3. **Clear memory between batches:**
   ```python
   import gc
   for batch in batches:
       results = detector.detect(batch)
       del batch
       gc.collect()
   ```

4. **Use smaller model:**
   ```python
   detector = YOLODetector(model_path='yolov8n.pt')  # Nano model
   ```

---

### Symptom: Memory leak on repeated detections

**Solutions:**

1. **Explicitly clean up:**
   ```python
   del detector
   import torch
   if torch.cuda.is_available():
       torch.cuda.empty_cache()
   ```

2. **Use context manager:**
   ```python
   with BatchProcessor() as processor:
       results = processor.process_batch(images)
   ```

3. **Monitor memory:**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

---

## Device Compatibility Problems

### Error: MPS (Apple Silicon) not working

**Symptom:**
```
RuntimeError: MPS backend not available
```

**Solution:**
1. Ensure you're on Apple Silicon (M1/M2/M3)
2. Install MPS-enabled PyTorch:
   ```bash
   pip install torch torchvision
   ```
3. Verify MPS availability:
   ```python
   import torch
   print(torch.backends.mps.is_available())  # Should be True
   ```

4. Use MPS device:
   ```python
   device_manager = DeviceManager(device='mps')
   ```

---

### Error: ARM64 compatibility issues

**Symptom:**
```
ImportError: cannot import name '_C' from 'torch'
```

**Solution:**
1. Ensure you're using ARM64-compatible Python:
   ```bash
   python --version  # Should show ARM or aarch64
   ```

2. Install ARM64-specific packages:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

3. For Raspberry Pi:
   ```bash
   pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/linux/arm64
   ```

---

## Detection Accuracy Issues

### Symptom: Too many false positives

**Solutions:**

1. **Increase confidence threshold:**
   ```python
   detector = YOLODetector(
       model_path='yolov8n.pt',
       confidence_threshold=0.7  # Higher = fewer false positives
   )
   ```

2. **Increase IOU threshold for NMS:**
   ```python
   detector = YOLODetector(
       model_path='yolov8n.pt',
       iou_threshold=0.5  # Higher = stricter NMS
   )
   ```

3. **Use larger model:**
   ```python
   detector = YOLODetector(model_path='yolov8s.pt')  # More accurate
   ```

---

### Symptom: Missing detections (false negatives)

**Solutions:**

1. **Decrease confidence threshold:**
   ```python
   detector = YOLODetector(
       model_path='yolov8n.pt',
       confidence_threshold=0.3  # Lower = more detections
   )
   ```

2. **Use larger model:**
   ```python
   detector = YOLODetector(model_path='yolov8m.pt')  # Better accuracy
   ```

3. **Improve image quality:**
   ```python
   # Enhance contrast
   image = cv2.convertScaleAbs(image, alpha=1.5, beta=0)
   ```

4. **Ensure correct input size:**
   ```python
   # YOLOv8 works best with 640x640
   image = cv2.resize(image, (640, 640))
   ```

---

### Symptom: Poor bounding box accuracy

**Solutions:**

1. **Use higher resolution input:**
   ```python
   image = cv2.resize(image, (1280, 1280))  # Higher res
   ```

2. **Use larger model:**
   ```python
   detector = YOLODetector(model_path='yolov8x.pt')  # Best accuracy
   ```

3. **Fine-tune model on your data:**
   ```python
   # Train custom model (Ultralytics)
   yolo detect train data=custom.yaml model=yolov8n.pt epochs=100
   ```

---

## Configuration Problems

### Error: Invalid YAML syntax

**Symptom:**
```
yaml.scanner.ScannerError: while scanning a mapping
```

**Solution:**
1. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. Check indentation (use spaces, not tabs):
   ```yaml
   # Good
   model:
     type: yolo_v8

   # Bad - mixed tabs and spaces
   model:
     type: yolo_v8
   ```

3. Use YAML validator: https://www.yamllint.com/

---

### Error: Configuration validation failed

**Symptom:**
```
ValidationError: confidence_threshold must be between 0.0 and 1.0
```

**Solution:**
1. Check value ranges:
   - `confidence_threshold`: 0.0 to 1.0
   - `iou_threshold`: 0.0 to 1.0
   - `max_detections`: > 0

2. Fix configuration:
   ```yaml
   # Bad
   detection:
     confidence_threshold: 1.5  # Invalid!

   # Good
   detection:
     confidence_threshold: 0.5  # Valid
   ```

3. Use profile manager:
   ```python
   from src.config.profile_manager import ProfileManager
   manager = ProfileManager()
   config = manager.load_profile('prod')  # Pre-validated
   ```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs:**
   ```bash
   tail -f logs/edge_detection.log
   ```

2. **Enable verbose logging:**
   ```bash
   edge-detection detect image.jpg --verbose
   ```

3. **Run diagnostics:**
   ```python
   from src.hardware.device_manager import DeviceManager
   manager = DeviceManager(device='auto')
   print(manager.get_device_info())
   ```

4. **Report issues:**
   - GitHub Issues: [Project Repository]
   - Include: Error message, code snippet, system info

5. **Community resources:**
   - Documentation: [Full Docs]
   - Examples: `examples/` directory
   - FAQ: Check existing issues first

---

## Quick Reference

### Check System Compatibility

```python
import torch
import platform

print(f"Python: {platform.python_version()}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"MPS Available: {torch.backends.mps.is_available()}")
```

### Reset Everything

```bash
# Remove all cached models
rm -rf models/

# Remove virtual environment
rm -rf venv/

# Create fresh environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Performance Checklist

- [ ] Using GPU (CUDA/MPS)?
- [ ] Using appropriate model size (n/s/m/l/x)?
- [ ] Image resolution reasonable (640x640)?
- [ ] Confidence threshold appropriate (0.3-0.7)?
- [ ] Using ONNX for production?
- [ ] Batch processing for multiple images?
- [ ] Memory cleared between runs?
