"""
Performance benchmark suite.

This package contains performance benchmarks for validating:
- Abstraction layer overhead
- ONNX vs PyTorch performance
- Quantization effectiveness
- Async and batch processing throughput

Run benchmarks:
  pytest tests/performance/ -m benchmark

Run smoke tests (quick check):
  pytest tests/performance/ -m smoke
"""
