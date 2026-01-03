# Performance Tuning Guide

## Hardware-Specific Optimization Recommendations

This guide provides hardware-specific recommendations for optimal performance of the real-time edge detection system.

## Hardware Configurations

### CPU: x86_64 (Intel/AMD)

**Recommended Backend: ONNX Runtime**

**Why:** ONNX Runtime provides the best CPU performance through:
- Optimized operator implementations
- Graph optimizations
- Multi-threading support
- CPU-specific instruction sets (AVX, AVX2, AVX512)

**Configuration:**
```yaml
model:
  backend: onnx
  device: cpu
  num_threads: 4  # Adjust based on CPU cores

inference:
  optimization_level: 2  # Enable all optimizations
  enable_profiling: false
```

**Performance Expectations:**
- Latency: 20-30ms per frame (640x640)
- Throughput: 30-50 FPS
- Memory: 300-500MB

**Tuning Tips:**
1. Set `num_threads` to physical core count (not hyperthreads)
2. Enable ONNX graph optimizations
3. Use INT8 quantization for 2-3x speedup
4. Disable unnecessary preprocessing steps

### GPU: NVIDIA (CUDA)

**Recommended Backend: TensorRT with INT8**

**Why:** TensorRT provides the lowest latency on NVIDIA GPUs through:
- Layer fusion
- Precision calibration (FP16, INT8)
- Kernel auto-tuning
- Dynamic tensor memory

**Configuration:**
```yaml
model:
  backend: tensorrt
  device: cuda
  precision: int8  # or fp16

inference:
  batch_size: 1  # For real-time, use batch_size=1
  max_workspace_size: 1GB
  enable_fp16: true
```

**Performance Expectations:**
- Latency: 5-10ms per frame (640x640)
- Throughput: 100-200 FPS
- Memory: 500-800MB (GPU)

**Tuning Tips:**
1. Use INT8 calibration for best performance
2. Optimize batch size for your use case
3. Enable DLA (Deep Learning Accelerator) on Jetson devices
4. Profile with Nsight to identify bottlenecks

### GPU: Apple Silicon (M1/M2/M3)

**Recommended Backend: PyTorch MPS**

**Why:** MPS (Metal Performance Shaders) provides native optimization for Apple Silicon:
- Unified memory architecture
- Metal shader optimizations
- Low-latency inference

**Configuration:**
```yaml
model:
  backend: pytorch
  device: mps

inference:
  enable_mps_graph: true
```

**Performance Expectations:**
- Latency: 8-15ms per frame (640x640)
- Throughput: 60-120 FPS
- Memory: 400-600MB

**Tuning Tips:**
1. Use MPS graph mode for better performance
2. Enable FP16 for reduced memory usage
3. Batch processing can improve throughput

### Edge TPU (Coral)

**Recommended Backend: TFLite with Edge TPU**

**Why:** Edge TPU provides hardware acceleration for edge devices:
- Dedicated AI accelerator
- Ultra-low power consumption
- Deterministic latency

**Configuration:**
```yaml
model:
  backend: tflite
  device: tpu
  model_path: models/edgetpu/yolov8n_edgetpu.tflite

inference:
  delegate: edgetpu
  num_threads: 1  # Edge TPU handles threading
```

**Performance Expectations:**
- Latency: 10-20ms per frame
- Throughput: 50-100 FPS
- Memory: 100-200MB
- Power: 2W

**Tuning Tips:**
1. Use Edge TPU compiler for model conversion
2. Quantize to INT8 (required for Edge TPU)
3. Optimize input size for TPU constraints
4. Use multiple TPUs for parallel inference

### NVIDIA Jetson (Nano, TX2, Xavier, Orin)

**Recommended Backend: TensorRT + DLA**

**Why:** Jetson devices have dedicated DLAs (Deep Learning Accelerators):
- Lower power than GPU
- Deterministic latency
- Offloads GPU for other tasks

**Configuration:**
```yaml
model:
  backend: tensorrt
  device: cuda
  use_dla: true  # Use DLA if available
  dla_core: 0

inference:
  precision: int8
  max_batch_size: 1
```

**Performance Expectations:**
- Latency: 15-25ms per frame (Jetson Xavier NX)
- Throughput: 40-60 FPS
- Memory: 400-600MB
- Power: 10-15W

**Tuning Tips:**
1. Use Jetson Power mode: MAXN for performance, 15W for power efficiency
2. Enable DLA for offloading
3. Use INT8 for best performance
4. Consider JetPack optimization tools

## Performance Thresholds (NFRs)

### NFR-P1: CPU Latency
- **Requirement:** Max 30ms inference latency on CPU
- **Validation:** `pytest tests/performance/test_onnx.py::test_onnx_latency`
- **Target:** ONNX Runtime, optimized graph

### NFR-P2: GPU Latency
- **Requirement:** Max 10ms inference latency on GPU/TPU
- **Validation:** `pytest tests/performance/test_onnx.py::test_tensorrt_latency`
- **Target:** TensorRT INT8 or Edge TPU

### NFR-P3: Throughput
- **Requirement:** Min 30 FPS sustained throughput
- **Validation:** `pytest tests/performance/test_async_batch.py::test_async_throughput`
- **Target:** Batch processing or async execution

### NFR-P4: Memory
- **Requirement:** Max 500MB memory usage
- **Validation:** `pytest tests/performance/test_async_batch.py::test_memory_within_limits`
- **Target:** INT8 quantization, optimized model

## Optimization Techniques

### 1. Model Selection

**YOLOv8 Model Comparison:**

| Model | Size (MB) | mAP | Latency (CPU) | Latency (GPU) |
|-------|-----------|-----|---------------|---------------|
| yolov8n | 6.0 | 37.3 | 25ms | 5ms |
| yolov8s | 18.5 | 44.9 | 40ms | 8ms |
| yolov8m | 49.7 | 50.2 | 70ms | 12ms |
| yolov8l | 83.7 | 52.9 | 110ms | 18ms |
| yolov8x | 130.5 | 54.5 | 170ms | 25ms |

**Recommendation:** Start with `yolov8n` for real-time edge applications.

### 2. Quantization

**INT8 Quantization Benefits:**
- 2-3x faster inference
- ~75% model size reduction
- Lower memory bandwidth
- <2% accuracy loss (when calibrated properly)

**When to Use:**
- CPU deployment (use ONNX INT8)
- GPU deployment (use TensorRT INT8)
- Edge TPU (requires INT8)

**Accuracy Validation:**
```bash
# Run accuracy validation before/after quantization
pytest tests/performance/test_quantization.py::test_accuracy_impact
```

### 3. Input Resolution

**Common Resolutions:**

| Resolution | Latency (ms) | Accuracy | Use Case |
|------------|--------------|----------|----------|
| 320x320 | 8ms | Lower | Fast detection, low accuracy |
| 640x640 | 25ms | Good | Standard real-time |
| 1280x1280 | 100ms | Higher | High accuracy, slower |

**Recommendation:** Use 640x640 for balanced performance/accuracy.

### 4. Preprocessing Optimization

**Tips:**
- Use OpenCV for image operations (faster than PIL)
- Disable unnecessary augmentations
- Use GPU preprocessing if available
- Batch preprocessing for multiple frames

### 5. Postprocessing Optimization

**Tips:**
- Use vectorized NumPy operations
- Limit max detections (e.g., top 100)
- Use efficient NMS implementation
- Filter low-confidence detections early

## Benchmarking

### Run Benchmarks

```bash
# Quick smoke test (< 1 minute)
python scripts/run_benchmarks.py --smoke

# Full benchmark suite (~5 minutes)
python scripts/run_benchmarks.py

# Check for regression
python scripts/check_regression.py benchmark_results_full.json
```

### Generate Baseline

```bash
# Generate baseline on current hardware
python scripts/run_benchmarks.py --output baselines/performance_baseline.json
```

### Compare Hardware

Run benchmarks on different hardware platforms to create comparison matrix:

```bash
# CPU
pytest tests/performance/ -k cpu -v

# GPU
pytest tests/performance/ -k gpu -v

# TPU
pytest tests/performance/ -k tpu -v
```

## Troubleshooting

### High CPU Latency

**Symptoms:** CPU latency > 30ms

**Solutions:**
1. Verify ONNX Runtime is being used (not PyTorch)
2. Check if graph optimizations are enabled
3. Reduce input resolution
4. Use INT8 quantization
5. Increase thread count (but not beyond physical cores)

### High GPU Latency

**Symptoms:** GPU latency > 10ms

**Solutions:**
1. Verify TensorRT is being used
2. Enable FP16 or INT8 precision
3. Check GPU utilization (should be > 80%)
4. Reduce batch size to 1 for real-time
5. Profile with Nsight to find bottlenecks

### Low Throughput

**Symptoms:** FPS < 30

**Solutions:**
1. Use batch processing
2. Enable async execution
3. Use multiple workers
4. Optimize data pipeline
5. Reduce I/O overhead

### High Memory Usage

**Symptoms:** Memory > 500MB

**Solutions:**
1. Use INT8 quantization
2. Reduce input resolution
3. Use smaller model (yolov8n)
4. Clear cache between batches
5. Check for memory leaks

### Poor Accuracy After Quantization

**Symptoms:** Accuracy loss > 2%

**Solutions:**
1. Ensure proper calibration dataset (100-1000 images)
2. Use representative calibration data
3. Try post-training quantization with fine-tuning
4. Check if model supports INT8 (some operations don't)
5. Consider FP16 as alternative

## Continuous Monitoring

### CI/CD Integration

The `.github/workflows/benchmark.yml` workflow:

1. Runs smoke tests on every PR
2. Runs full benchmarks on main branch
3. Checks for regression vs baseline
4. Posts results as PR comments

### Performance Tracking

Track performance over time:
- Commit benchmarks to repository
- Plot metrics in GitHub Actions
- Alert on significant regression
- Document optimization changes

## Best Practices

1. **Always benchmark on target hardware** - Development machine results may not match
2. **Use realistic input data** - Test with actual camera images, not random noise
3. **Measure multiple iterations** - Take median, not mean (outliers skew results)
4. **Monitor temperature and power** - Throttling affects performance
5. **Document all optimizations** - Keep track of what works and what doesn't
6. **Test edge cases** - Empty frames, crowded scenes, lighting changes
7. **Profile before optimizing** - Identify actual bottlenecks first
8. **Validate accuracy** - Don't sacrifice accuracy for speed

## Resources

- [ONNX Runtime Performance](https://onnxruntime.ai/docs/performance/)
- [TensorRT Best Practices](https://docs.nvidia.com/deeplearning/tensorrt/best-practices/index.html)
- [PyTorch MPS](https://pytorch.org/docs/stable/notes/mps.html)
- [Coral Edge TPU](https://coral.ai/docs/edgetpu/benchmarks/)
- [Jetson Tuning Guide](https://developer.nvidia.com/embedded/jetson-platform/benchmarks)
