# Claude Code Instructions for Real-time Edge Detection Project

## Project Overview
Real-time object detection system optimized for edge devices using YOLO models. Focus on performance, quantization, and deployment flexibility.

## Repository Structure

### Core Directories
- `src/`: Main source code
  - `detection/`: Detection implementations (YOLOv8, YOLOv10, ONNX)
  - `models/`: Model management, versioning, quantization
  - `device/`: Hardware detection and selection
  - `cli/`: Command-line interface
  - `metrics/`: Performance metrics collection
  - `config/`: Configuration management
  - `api/`: Async detection APIs
  - `preprocessing/`: Image preprocessing
  - `hardware/`: Device capability detection

- `tests/`: Test suite
  - `unit/`: Unit tests
  - `integration/`: Integration tests
  - `performance/`: Performance benchmarks
  - `security/`: Security tests

- `config/`: YAML configuration files
- `docs/`: Project documentation
- `examples/`: Usage examples

## Development Guidelines

### Code Style
- Python 3.13+ compatible
- Type hints required for all functions
- Docstrings for all public APIs
- Follow PEP 8 conventions
- Maximum line length: 100 characters

### Testing Requirements
- Unit tests for all new functions
- Integration tests for workflows
- Minimum 80% code coverage
- Performance benchmarks for optimization work
- Regression tests for critical paths

### Performance Standards
- Target: < 30ms inference time (640x640)
- Memory efficiency for edge deployment
- Async processing for video streams
- Quantization support (INT8/FP16)

## Common Commands

### Development
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/unit/test_config.py -v

# Run linting (if available)
ruff check src/ tests/
# or
black --check src/ tests/
```

### Detection
```bash
# Image detection
python run.py detect image.jpg --show

# Webcam detection
python run.py webcam

# Video processing
python run.py video input.mp4 --output output.mp4

# Benchmark
python run.py benchmark --iterations 100
```

## Project Status

### Completed Epics
- **Epic 1**: YAML configuration system, device selection, basic CLI
- **Epic 2**: Model abstraction, versioning, ONNX conversion, async API (partially)

### In Progress
- **Epic 2**: Model versioning and compatibility checking
- **Epic 4**: Advanced features (video streaming, tracking, deployment)

### Pending
- **Epic 3**: Observability, error handling, comprehensive testing, documentation

## Architecture Decisions

### Model Abstraction
- Factory pattern for model creation (`detection/factory.py`)
- Base detector interface (`detection/base.py`)
- Support for multiple YOLO versions

### Device Management
- Automatic device detection (`device/device_manager.py`)
- CPU/GPU/TPU support
- Performance-based device selection

### Configuration
- YAML-based configuration (`config/`)
- Profile-based settings (dev, prod, testing)
- Validation and defaults

### Performance Optimization
- ONNX conversion and optimization
- Quantization pipeline (INT8/FP16)
- Async batch processing
- Caching and memoization

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies
- Cover edge cases and error paths

### Integration Tests
- Test workflows end-to-end
- Real model inference (small models)
- Device-specific tests

### Performance Tests
- Benchmark inference time
- Memory usage profiling
- Regression detection

### Security Tests
- Input validation
- Model file security
- Secret masking in logs

## Documentation Requirements

### API Documentation
- All public functions need docstrings
- Parameters and return types documented
- Usage examples for complex APIs

### User Documentation
- CLI command reference
- Configuration guide
- Troubleshooting guide
- Performance tuning guide

## Workflow Integration

### BMAD Workflows
- Located in `_bmad/bmm/workflows/`
- Automated testing, code review, and documentation
- Progress tracking in `sprint-status.yaml`

### Story Development
1. Story created with acceptance criteria
2. Implementation with comprehensive tests
3. Automated code review
4. Integration and performance testing
5. Documentation updates

## Quality Gates

### Before Committing
- All tests pass: `pytest tests/`
- Coverage meets threshold: `pytest --cov=src tests/`
- No regressions: `pytest tests/performance/test_regression.py`
- Documentation updated

### Before PR Merge
- Code review completed
- Integration tests pass
- Performance benchmarks meet targets
- Security scans pass

## Performance Optimization Priorities

1. **Inference Speed**: < 30ms target
2. **Memory Efficiency**: Edge device constraints
3. **Batch Processing**: Async video processing
4. **Model Size**: Quantization and optimization
5. **Startup Time**: Fast model loading

## Security Considerations

- Validate all user inputs
- Secure model file loading
- No hardcoded credentials
- Secret masking in logs
- Dependency vulnerability scanning