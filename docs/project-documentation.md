# Realtime Edge Detection - Project Documentation

**Generated:** 2026-01-03  
**Status:** Phase 1 Implementation In Progress (4/31 stories complete)  
**Epic:** 1 - Project Setup & Basic Detection

## Project Overview

Realtime edge detection toolkit providing high-performance object detection optimized for edge devices. Built with Python, supports YOLO models (v8, v10), multiple hardware backends (CPU, CUDA, MPS, TFLite, ONNX), and comprehensive configuration management.

## Technology Stack

- **Language:** Python 3.11+
- **Core Libraries:**
  - PyYAML - Configuration management
  - Pydantic v2.0+ - Configuration validation
  - Ultralytics - YOLO model support
  - OpenCV - Image processing
- **Testing:** pytest, pytest-cov
- **Deployment:** Docker, Kubernetes (planned)

## Architecture

### Module Structure

```
src/
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── config_manager.py      # ConfigManager class with YAML/env loading
│   ├── validation.py          # Pydantic validation schemas
│   ├── profile_manager.py     # Profile-based configuration
│   └── defaults.py            # Default configuration values
├── models/                    # Model management (planned)
├── detection/                 # Detection engine (planned)
└── cli/                       # Command-line interface (planned)
```

### Configuration System

**Multi-layer configuration loading (priority highest to lowest):**
1. Environment variables (`EDGE_DETECTION_*`)
2. User config (`~/.config/edge-detection/config.yaml`)
3. Project config (`./config/config.yaml`)
4. Profile config (`config/{profile}.yaml`)
5. Default values (hardcoded)

**Key Features:**
- Deep merge for nested structures
- Type-safe validation with Pydantic
- Profile-based configurations (dev, prod, testing)
- Clear error messages with fix suggestions
- Environment variable override with automatic type conversion

## Implementation Progress

### Completed Stories (Epic 1)

✅ **Story 1.1: YAML Configuration System**
- ConfigManager class with singleton pattern
- YAML loading from multiple sources
- Environment variable override with `EDGE_DETECTION_` prefix
- Deep configuration merging
- Comprehensive error handling

✅ **Story 1.2: Configuration Validation and Profiles**
- Pydantic-based validation schema
- Profile management (dev, prod, testing)
- Range validators (confidence: 0.0-1.0, IoU: 0.0-1.0)
- Enum validators (device type, model type)
- Profile merging precedence

✅ **Story 1.3: Model Download and Caching**
- Automatic model download on first use
- Local caching in `~/.cache/edge-detection/models/`
- Progress tracking for downloads
- Retry logic (3 attempts)
- Model integrity validation

✅ **Story 1.4: Device Detection and Selection**
- Auto device detection (CUDA → MPS → TFLite → CPU)
- Manual device selection via CLI/config
- Multi-GPU support
- Graceful fallback to CPU
- Clear error messages for unavailable devices

### Test Coverage

- **Overall:** 34% (ConfigManager: 38%)
- **Unit Tests:** 51 tests covering configuration, validation, profiles
- **Integration Tests:** 18 tests for end-to-end scenarios

## Design Patterns

### Configuration Management
- **Singleton Pattern:** Single ConfigManager instance
- **Builder Pattern:** Layered configuration building
- **Strategy Pattern:** Multiple config sources with unified interface

### Error Handling
- Custom exceptions: `ConfigurationError`, `ValidationError`
- Clear error messages with resolution hints
- Comprehensive logging at appropriate levels

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all public functions
- Docstrings for all classes and public methods
- Maximum line length: 100 characters

### Testing Standards
- Minimum 80% test coverage
- Red-Green-Refactor TDD cycle
- Unit tests for business logic
- Integration tests for component interactions
- Test fixtures for consistent test data

### Configuration Standards
- All defaults in `defaults.py`
- User configs in `~/.config/edge-detection/`
- Project configs in `./config/`
- Environment variables use `EDGE_DETECTION_` prefix

## Next Steps

### Immediate (Epic 1 Completion)
- Story 1.5: Basic detection CLI
- Story 1.6: Unit test coverage enhancement
- Story 1.7: Code refactoring

### Short-term (Epic 2)
- Model abstraction layer
- ONNX conversion and optimization
- Quantization pipeline (INT8/FP16)
- Batch processing CLI

### Long-term (Epics 3-4)
- Production monitoring and logging
- Video streaming support
- Multi-object tracking
- Containerization and deployment

## Dependencies

```
PyYAML>=6.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

## Configuration Examples

### Basic Config
```yaml
model:
  type: yolo_v8
  path: yolov8n.pt

device:
  type: auto

detection:
  confidence_threshold: 0.5
  iou_threshold: 0.4
```

### Environment Variables
```bash
export EDGE_DETECTION_MODEL__PATH=/custom/path/to/model.pt
export EDGE_DETECTION_DETECTION__CONFIDENCE_THRESHOLD=0.7
export EDGE_DETECTION_DEVICE__TYPE=cuda
```

## Known Limitations

- Only 4/31 stories implemented
- Limited to configuration and device detection
- No detection functionality yet
- No CLI interface yet
- Test coverage below 80% target

## References

- **PRD:** `_bmad-output/planning-artifacts/02-PRD.md`
- **Architecture:** `_bmad-output/planning-artifacts/03-ARCHITECTURE.md`
- **Epics:** `_bmad-output/planning-artifacts/epics.md`
- **Test Design:** `_bmad-output/test-artifacts/test-design-epic-1.md`
