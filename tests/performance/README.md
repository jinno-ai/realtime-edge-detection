# Performance Benchmark Suite

This directory contains comprehensive performance benchmarks for the real-time edge detection system.

## Overview

The benchmark suite validates performance requirements and detects regressions early in development.

## Benchmark Categories

### 1. Abstraction Layer (`test_abstraction.py`)
- Measures overhead of `AbstractDetector` vs direct implementation
- **Threshold:** < 5% overhead
- **Status:** Ready for implementation

### 2. ONNX Performance (`test_onnx.py`)
- Compares ONNX Runtime vs PyTorch on CPU
- **Target:** 1.5-2x speedup, <1% accuracy loss
- **Status:** Requires ONNX conversion (Story 2.3)

### 3. Quantization (`test_quantization.py`)
- Evaluates INT8/FP16 vs FP32 performance
- **Target:** 2-3x speedup, <2% accuracy loss, ~75% size reduction
- **Status:** Requires quantization pipeline (Story 2.4)

### 4. Async/Batch Processing (`test_async_batch.py`)
- Measures throughput improvements from async and batch execution
- **Target:** 1.5x throughput gain, non-blocking
- **Status:** Requires async API (Story 2.6)

### 5. Infrastructure Tests (`test_benchmark_infrastructure.py`)
- Validates measurement accuracy
- Tests regression detection
- **Status:** Complete

## Running Benchmarks

### Quick Smoke Test (Recommended for PR checks)
```bash
# Runs in < 2 minutes
pytest tests/performance/ -m smoke -v
```

### Full Benchmark Suite
```bash
# Runs in ~5-10 minutes
pytest tests/performance/ -m benchmark -v
```

### Specific Benchmark Category
```bash
# Test abstraction overhead
pytest tests/performance/test_abstraction.py -v

# Test ONNX performance
pytest tests/performance/test_onnx.py -v

# Test quantization
pytest tests/performance/test_quantization.py -v

# Test async/batch
pytest tests/performance/test_async_batch.py -v
```

### Using Benchmark Runner Script
```bash
# Smoke tests
python scripts/run_benchmarks.py --smoke

# Full benchmarks
python scripts/run_benchmarks.py --output results.json

# Check for regression
python scripts/check_regression.py results.json
```

## Test Markers

- `@pytest.mark.smoke`: Quick performance checks (< 2 min total)
- `@pytest.mark.benchmark`: Detailed benchmarks
- `@pytest.mark.slow`: Very slow tests (> 1 min each)

## Baseline Management

### View Current Baseline
```bash
cat baselines/performance_baseline.json
```

### Create New Baseline
```bash
# Run benchmarks
pytest tests/performance/ -m benchmark

# Save results as baseline
python scripts/run_benchmarks.py --output baselines/performance_baseline.json
```

### Update Baseline (After Validated Improvements)
```bash
python scripts/check_regression.py results.json --update-baseline
```

## Performance Thresholds

Defined in `conftest.py`:

```python
PERFORMANCE_THRESHOLDS = {
    'abstraction_overhead': 0.05,  # 5% max
    'onnx_speedup': 1.5,           # 1.5x min
    'quantization_speedup': 2.0,   # 2x min
    'quantization_accuracy_loss': 0.02,  # 2% max
    'async_speedup': 1.5,          # 1.5x min
    'cpu_latency_ms': 30,          # NFR-P1
    'gpu_latency_ms': 10,          # NFR-P2
    'fps': 30,                     # NFR-P3
    'memory_mb': 500               # NFR-P4
}
```

## CI/CD Integration

The `.github/workflows/benchmark.yml` workflow:

1. **Smoke tests on every PR** - Catches major regressions
2. **Full benchmarks on main** - Establishes performance history
3. **Regression detection** - Fails if performance degrades >10%
4. **PR comments** - Posts benchmark results as comments

## Interpreting Results

### Benchmark Result Format

```json
{
  "benchmarks": {
    "abstraction_overhead": {
      "baseline_ms": 25.0,
      "current_ms": 25.8,
      "overhead_percent": 3.2,
      "status": "PASS",
      "threshold": "5%"
    },
    "onnx_vs_pytorch": {
      "pytorch_ms": 25.0,
      "onnx_ms": 14.5,
      "speedup": 1.72,
      "status": "PASS",
      "threshold": "1.5x"
    }
  }
}
```

### Failure Messages

**Abstraction Overhead Fail:**
```
❌ FAIL: Abstraction overhead exceeds threshold

Baseline latency: 25.0ms
Current latency: 28.5ms
Overhead: 14.0% (threshold: 5%)

💡 Possible causes:
   1. Unnecessary method calls in AbstractDetector
   2. Excessive validation logic
   3. Inefficient data copying
```

**ONNX Speedup Fail:**
```
❌ FAIL: ONNX speedup below threshold

PyTorch: 25.0ms
ONNX: 20.0ms
Speedup: 1.25x (threshold: 1.5x)

💡 Possible causes:
   1. ONNX graph not optimized
   2. Unsupported operators causing fallback
   3. Suboptimal opset version
```

## Hardware-Specific Recommendations

See `/docs/performance_tuning_guide.md` for detailed recommendations:

- **CPU:** Use ONNX Runtime with INT8 quantization
- **NVIDIA GPU:** Use TensorRT with FP16/INT8
- **Apple Silicon:** Use PyTorch MPS backend
- **Edge TPU:** Use TFLite with INT8
- **Jetson:** Use TensorRT + DLA

## Troubleshooting

### Tests Are Skipped

Many benchmarks are currently skipped because they require:
- Model files (download with Story 1.3)
- ONNX conversion (Story 2.3)
- Quantization pipeline (Story 2.4)
- Async API (Story 2.6)

These will be enabled as those stories are implemented.

### High Variance in Results

- **Use median, not mean** - Outliers can skew results
- **Ensure consistent hardware** - Close other applications
- **Check for throttling** - Monitor temperature
- **Run multiple iterations** - 10+ for stable results

### CI/CD Failures

1. Check if regression is real or hardware variance
2. If real performance issue: fix and re-run
3. If hardware variance: consider increasing threshold
4. Document any intentional performance changes

## Contributing

When adding new benchmarks:

1. Follow existing test structure
2. Use fixtures from `conftest.py`
3. Add appropriate marker (`@pytest.mark.smoke` or `@pytest.mark.benchmark`)
4. Document thresholds and expectations
5. Update baseline after validation

## Performance Profiles

Different use cases require different optimizations:

### Real-Time Edge (30 FPS @ 640x640)
- Model: YOLOv8n
- Backend: ONNX Runtime or TensorRT
- Quantization: INT8
- Expected: 20-30ms latency

### High Accuracy (10 FPS @ 1280x1280)
- Model: YOLOv8m
- Backend: TensorRT
- Quantization: FP16
- Expected: 80-100ms latency

### Ultra-Low Power (10 FPS @ 320x320)
- Model: YOLOv8n
- Backend: TFLite Edge TPU
- Quantization: INT8
- Expected: 50-100ms latency, 2W power

## Resources

- [Performance Tuning Guide](../../docs/performance_tuning_guide.md)
- [NFR Requirements](../../_bmad-output/planning-artifacts/02-PRD.md)
- [Regression Detection Script](../../scripts/check_regression.py)
- [Benchmark Runner Script](../../scripts/run_benchmarks.py)
