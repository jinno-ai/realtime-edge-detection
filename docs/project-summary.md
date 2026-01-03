# Realtime Edge Detection - Project Documentation

**Generated:** 2026-01-03
**Project:** realtime-edge-detection
**Status:** Phase 2 Implementation (8/31 stories complete)

---

## Project Overview

**Purpose:** Real-time object detection system using YOLO models (v8/v10) with support for multiple deployment scenarios (edge, cloud, batch processing).

**Tech Stack:**
- **Language:** Python 3.10+
- **ML Framework:** PyTorch, Ultralytics YOLO
- **Detection:** YOLOv8, YOLOv10, Custom models
- **Configuration:** YAML with environment variable overrides
- **Testing:** pytest with coverage reporting

---

## Architecture

### Core Components

1. **Configuration System** (`src/config/`)
   - ConfigManager: YAML + env var loading
   - Validation: Pydantic-based config validation
   - Profiles: Development/Production configurations

2. **Detection System** (`src/detection/`)
   - AbstractDetector: Base detector interface
   - YOLOv8Detector: YOLOv8 implementation
   - YOLOv10Detector: YOLOv10 implementation
   - CustomDetector: Custom .pt/.onnx models
   - DetectorFactory: Detector instantiation

3. **CLI Interface** (`src/cli/`)
   - `edge-detection detect`: Image/video detection
   - `edge-detection config`: Configuration management
   - Output formats: JSON, CSV, visual annotations

---

## Implementation Status

### Completed Stories (8/31)

**Epic 1: Project Setup & Basic Detection** ✅
- ✅ Story 1-1: YAML Configuration System
- ✅ Story 1-2: Configuration Validation & Profiles
- ✅ Story 1-3: Model Download & Caching
- ✅ Story 1-4: Device Detection & Selection
- ✅ Story 1-5: Basic Detection CLI
- ✅ Story 1-6: Unit Test Coverage
- ✅ Story 1-7: Code Refactoring

**Epic 2: Model Flexibility & Optimization** (1/7 complete)
- ✅ Story 2-1: Abstract Model Interface

### Incomplete Stories (23/31)

**Epic 2:** Stories 2-2 through 2-7 (missing Tasks/Subtasks)
**Epic 3:** All stories (missing Tasks/Subtasks)
**Epic 4:** All stories (missing Tasks/Subtasks)

---

## Configuration

### Config File Locations

1. **User Config:** `~/.config/edge-detection/config.yaml`
2. **Project Config:** `./config/default.yaml`
3. **Environment Variables:** `EDGE_DETECTION_*`

### Configuration Priority

```
Environment Variables > YAML Config > Default Values
```

### Example Config

```yaml
model:
  name: yolov8n
  path: ~/.cache/edge-detection/models/

device:
  type: auto  # auto, cpu, cuda, mps

detection:
  confidence: 0.25
  iou: 0.45
  max_detections: 100

output:
  format: json  # json, csv, visual
  save_images: false
```

---

## Usage

### Basic Detection

```bash
# Detect objects in image
edge-detection detect --image path/to/image.jpg

# Detect with custom model
edge-detection detect --image image.jpg --model custom.pt

# Specify device
edge-detection detect --image image.jpg --device cuda

# Save visual output
edge-detection detect --image image.jpg --output-format visual --save-images
```

### Configuration Management

```bash
# Show current config
edge-detection config show

# Validate config
edge-detection config validate

# List available profiles
edge-detection config list-profiles
```

---

## Testing

### Test Status

- **Total Tests:** 385
- **Pass Rate:** ~85% (330/385)
- **Coverage:** 34% overall
- **Target:** 75% coverage

### Test Modules

1. **Config Tests:** 65 tests (84.6% pass)
2. **Detection Tests:** 28 tests (100% pass)
3. **CLI Tests:** 20+ tests (100% pass)
4. **Integration Tests:** TBD

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/config/ -v
pytest tests/detection/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Model Management

### Supported Models

- **YOLOv8:** yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
- **YOLOv10:** yolov10n, yolov10s
- **Custom:** Any .pt or .onnx model

### Model Cache

Models are cached in `~/.cache/edge-detection/models/`:

```
~/.cache/edge-detection/models/
├── yolov8n.pt
├── yolov8s.pt
├── archive/
└── onnx/  # For ONNX exports
```

### Model Download

Models download automatically on first use:

```bash
# First run - downloads model
edge-detection detect --image test.jpg

# Subsequent runs - uses cache
edge-detection detect --image test.jpg
```

---

## Project Structure

```
realtime-edge-detection/
├── src/
│   ├── config/           # Configuration system
│   ├── detection/        # Detection implementations
│   ├── cli/             # Command-line interface
│   └── utils/           # Utilities
├── tests/               # Test suite
│   ├── config/
│   ├── detection/
│   └── cli/
├── config/              # Config templates
│   ├── default.yaml
│   └── example.yaml
├── docs/                # Documentation
└── _bmad-output/        # BMAD artifacts
    ├── planning-artifacts/
    ├── implementation-artifacts/
    └── test-artifacts/
```

---

## Development Guidelines

### Coding Standards

1. **Type Hints:** Use for all public functions
2. **Docstrings:** Google style docstrings
3. **Error Handling:** Clear error messages with suggestions
4. **Testing:** >75% coverage required

### Architecture Patterns

1. **Abstract Base Classes:** Use for extensible interfaces
2. **Factory Pattern:** For object instantiation
3. **Singleton:** ConfigManager (single instance)
4. **Strategy Pattern:** Different detector types

### Code Quality

- **Linting:** ruff
- **Formatting:** black
- **Type Checking:** mypy (optional)

---

## Known Issues

### Critical Issues

1. **Test Failures:** 10/65 config tests failing
   - State pollution between tests
   - Validation issues with 'custom_model'
   - **Impact:** Medium
   - **Fix:** Add test fixtures, fix validation

2. **Low Coverage:** 34% vs 75% target
   - **Impact:** High
   - **Fix:** Add integration tests, edge cases

3. **Incomplete Stories:** 23/31 stories missing tasks
   - **Impact:** Blocking
   - **Fix:** Run create-story for incomplete stories

---

## Next Steps

### Immediate (This Sprint)

1. Fix 10 failing tests
2. Improve coverage to 75%
3. Complete remaining stories (2-2 through 4-11)

### Short-term (Next Sprint)

1. ONNX conversion and optimization (Epic 2)
2. Batch processing (Epic 2)
3. Async APIs (Epic 2)

### Long-term

1. Advanced logging (Epic 3)
2. Performance optimization (Epic 3)
3. Video streaming (Epic 4)
4. Deployment guides (Epic 4)

---

## References

- **Repository:** [GitHub URL]
- **Documentation:** `docs/`
- **BMAD Artifacts:** `_bmad-output/`
- **Test Reports:** `_bmad-output/test-artifacts/`

---

**Last Updated:** 2026-01-03
**Status:** Phase 2 Implementation (8/31 stories)
**Test Coverage:** 34% (Target: 75%)
**Next Milestone:** Complete Epic 2 (Model Flexibility)
