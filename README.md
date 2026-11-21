# realtime-edge-detection

Real-time object detection toolkit for edge devices — YOLOv8/v10 +
ONNX in Python. CLI, async API, config profiles, device detection,
benchmarks, and a real test suite.

> **Status**: active development has moved to
> [realtime-edge-detection-rs](https://github.com/jinno-ai/realtime-edge-detection-rs),
> a Rust port focused on the edge runtime path (inference → decode → NMS).
> This repo remains the original Python implementation — larger feature
> surface, heavier stack (torch + ultralytics).

## Structure

```
src/
  detection/   YOLOv8 & YOLOv10 detectors, factory, ONNX support
  models/      model management, versioning, quantization
  device/      hardware detection & selection (CPU/GPU)
  preprocessing/ letterbox, augmentation
  cli/         detect / batch / interactive / metrics commands
  api/         async detection API
  metrics/     performance metrics collection
  config/      YAML profiles with validation
tests/         unit + integration + performance + security suites
examples/      basic / batch / video-streaming / async usage
```

## Quick start

```sh
pip install -r requirements.txt

python run.py detect image.jpg          # single image
python run.py video input.mp4           # video processing
python run.py benchmark --iterations 100
pytest tests/                           # test suite
```

## Honest notes

- Built for edge-oriented workflows; absolute performance numbers depend
  on hardware and model choice — no unverified FPS claims here.
- Model weights are not committed; bring your own YOLO checkpoint or
  export via `yolo export`.
- Historical docs live in `docs/`; some predate the current code, so
  trust the code and tests first.
