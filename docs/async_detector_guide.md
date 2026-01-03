# AsyncDetector - Async and Batch Detection API

## Overview

`AsyncDetector` is a high-performance async and batch detection wrapper that enables efficient parallel processing of images and video streams. It provides a non-blocking interface for object detection using ThreadPoolExecutor-based parallel execution.

## Features

- **Asynchronous Detection**: Non-blocking detection API for concurrent image processing
- **Batch Processing**: Optimized batch detection with automatic chunking
- **Thread Pool Management**: Configurable worker threads for parallel execution
- **Error Handling**: Comprehensive error handling with partial batch failure support
- **Video Streaming**: Optimized for real-time video processing (30+ FPS)
- **Thread-Safe**: All operations are thread-safe

## Installation

The AsyncDetector is included in the main package:

```python
from src.api import AsyncDetector
from src.detection.yolov8 import YOLOv8Detector
```

## Quick Start

### Basic Async Detection

```python
import asyncio
from src.api import AsyncDetector
from src.detection.yolov8 import YOLOv8Detector

# Create base detector
base_detector = YOLOv8Detector()
base_detector.load_model('yolov8n.pt', device='cpu')

# Wrap with async interface
detector = AsyncDetector(base_detector, max_workers=4)

# Async detection
async def process_image(image):
    result = await detector.detect_async(image)
    return result

# Run
result = asyncio.run(process_image(image))
```

### Batch Detection

```python
# Batch detection
results = detector.detect_batch(images, batch_size=16)

# Or use async version
async def process_batch():
    results = await detector.detect_batch_async(images, batch_size=16)
    return results

results = asyncio.run(process_batch())
```

### Video Streaming

```python
import cv2

async def process_video_stream(video_path):
    cap = cv2.VideoCapture(video_path)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Async detection (non-blocking)
            detections = await detector.detect_async(frame_rgb)

            # Process detections...
            # Display/save results

    finally:
        cap.release()

# Run
asyncio.run(process_video_stream('video.mp4'))
```

## API Reference

### AsyncDetector

#### Constructor

```python
AsyncDetector(
    detector: AbstractDetector,
    max_workers: int = 4,
    default_batch_size: int = 16
)
```

**Parameters:**
- `detector`: Base detector implementing AbstractDetector interface
- `max_workers`: Maximum number of parallel worker threads (default: 4)
- `default_batch_size`: Default batch size for batch processing (default: 16)

#### Methods

##### `async detect_async(image: np.ndarray) -> DetectionResult`

Run asynchronous detection on a single image.

**Parameters:**
- `image`: Input image as numpy array (H, W, C) in RGB format

**Returns:**
- `DetectionResult` with boxes, scores, classes, and metadata

**Raises:**
- `RuntimeError`: If detector has been shutdown
- `ValueError`: If image format is invalid
- `Exception`: Propagates detection errors from underlying detector

**Example:**
```python
result = await detector.detect_async(image)
print(f"Detected {result.metadata['num_detections']} objects")
```

---

##### `detect_batch(images: List[np.ndarray], batch_size: Optional[int] = None) -> List[DetectionResult]`

Run batch detection on multiple images with automatic chunking.

**Parameters:**
- `images`: List of input images as numpy arrays
- `batch_size`: Batch size for processing (default: self.default_batch_size)

**Returns:**
- List of `DetectionResult` objects, one per input image

**Raises:**
- `RuntimeError`: If detector has been shutdown
- `ValueError`: If images list is empty or batch_size < 1
- `PartialBatchError`: If some images fail processing

**Example:**
```python
results = detector.detect_batch(images, batch_size=16)
print(f"Processed {len(results)} images")
```

---

##### `async detect_batch_async(images: List[np.ndarray], batch_size: Optional[int] = None) -> List[DetectionResult]`

Async version of `detect_batch` for use in async contexts.

**Parameters:**
- `images`: List of input images as numpy arrays
- `batch_size`: Batch size for processing

**Returns:**
- List of `DetectionResult` objects

**Example:**
```python
results = await detector.detect_batch_async(images, batch_size=16)
```

---

##### `shutdown(wait: bool = True)`

Shutdown the thread pool gracefully.

**Parameters:**
- `wait`: Whether to wait for pending tasks to complete (default: True)

**Example:**
```python
detector.shutdown()
```

---

##### `get_stats() -> Dict[str, Any]`

Get detector statistics.

**Returns:**
- Dictionary with detector stats (max_workers, default_batch_size, shutdown, detector_loaded)

**Example:**
```python
stats = detector.get_stats()
print(f"Max workers: {stats['max_workers']}")
```

### Utility Functions

#### `async detect_multiple_async(detector: AsyncDetector, images: List[np.ndarray]) -> List[DetectionResult]`

Detect multiple images in parallel using `asyncio.gather`.

**Parameters:**
- `detector`: AsyncDetector instance
- `images`: List of input images

**Returns:**
- List of `DetectionResult` objects

**Example:**
```python
from src.api.async_detector import detect_multiple_async

results = await detect_multiple_async(detector, images)
```

### Exceptions

#### `PartialBatchError`

Exception raised when batch detection partially fails.

**Attributes:**
- `message`: Error message
- `successful`: Number of successfully processed images
- `total`: Total number of images
- `results`: Partial results (images that succeeded)

**Example:**
```python
try:
    results = detector.detect_batch(images)
except PartialBatchError as e:
    print(f"Partial failure: {e.successful}/{e.total} succeeded")
    results = e.results  # Access partial results
```

## Performance Characteristics

### Async Detection

- **Throughput**: Up to 4x speedup with 4 workers
- **Latency**: Similar to single detection (~25ms)
- **Use Case**: Multiple concurrent images

### Batch Detection

- **Throughput**: Up to 14x speedup for large batches
- **Latency**: Higher per image, but much better overall throughput
- **Use Case**: Processing many images (100+)

### Video Streaming

- **Target**: 30+ FPS
- **Achieved**: Yes, with optimized configuration
- **Use Case**: Real-time video processing

## Configuration Tips

### Choose `max_workers` based on:

1. **CPU cores**: typically `min(4, cpu_count)`
2. **Model complexity**: lighter models can use more workers
3. **Memory**: more workers = more memory usage

### Choose `batch_size` based on:

1. **Available memory**: larger batches need more RAM/VRAM
2. **Throughput needs**: larger batches = better throughput
3. **Latency needs**: smaller batches = lower latency

### Recommended configurations:

```python
# Low latency (video streaming)
detector = AsyncDetector(base_detector, max_workers=4, default_batch_size=4)

# High throughput (batch processing)
detector = AsyncDetector(base_detector, max_workers=8, default_batch_size=32)

# Balanced
detector = AsyncDetector(base_detector, max_workers=4, default_batch_size=16)
```

## Best Practices

1. **Always shutdown**: Use context manager or call `shutdown()`
   ```python
   with AsyncDetector(base_detector, max_workers=4) as detector:
       results = detector.detect_batch(images)
   # Auto shutdown
   ```

2. **Handle errors gracefully**: Use try-except for async operations
   ```python
   try:
       result = await detector.detect_async(image)
   except Exception as e:
       print(f"Detection failed: {e}")
   ```

3. **Use appropriate batch size**: Match to your use case
   ```python
   # For real-time: small batches
   results = await detector.detect_batch_async(frames, batch_size=4)

   # For batch processing: large batches
   results = detector.detect_batch(images, batch_size=32)
   ```

4. **Monitor performance**: Use `get_stats()` to check configuration
   ```python
   stats = detector.get_stats()
   if not stats['detector_loaded']:
       print("Warning: Detector not loaded!")
   ```

## Testing

Run the comprehensive test suite:

```bash
# Run all async detector tests
pytest tests/api/test_async_detector.py -v

# Run with coverage
pytest tests/api/test_async_detector.py --cov=src/api --cov-report=html
```

## Examples

See the `examples/` directory for complete examples:

- `examples/async_detection.py` - Async detection examples
- `examples/batch_detection.py` - Batch processing examples
- `examples/video_streaming.py` - Video streaming examples

## Benchmarks

Run performance benchmarks:

```bash
python benchmarks/async_benchmark.py
```

This will compare:
- Synchronous detection
- Async detection
- Batch detection (various batch sizes)
- Video streaming performance
- Different worker counts

## License

Part of the Real-time Edge Detection Toolkit.

## Support

For issues, questions, or contributions, please refer to the main project documentation.
