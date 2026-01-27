# Agents for Real-time Edge Detection Project

## Project Context
This is a computer vision project focused on real-time object detection optimized for edge devices. The project uses YOLO models (YOLOv8, YOLOv10) with emphasis on performance optimization, quantization, and edge deployment.

## Available Agents

### Core BMAD Agents
- **bmm-dev**: Development and implementation tasks
- **bmm-architect**: Architecture design and decisions
- **bmm-analyst**: Requirements analysis and technical research
- **bmm-pm**: Project management and story creation
- **bmm-sm**: Scrum master and workflow coordination
- **bmm-tech-writer**: Documentation generation
- **bmm-tea**: Test engineering and automation
- **bmm-ux-designer**: User experience and interface design

### Project-Specific Agent Customization

#### bmm-dev Customization
- **Specialization**: Computer vision and edge deployment
- **Skills**: Python, OpenCV, ONNX, TensorRT, CUDA, ARM optimization
- **Focus Areas**: Model optimization, quantization, async processing, performance tuning
- **Testing**: pytest, benchmarking, regression testing

#### bmm-architect Customization
- **Domain**: Real-time systems and edge computing
- **Patterns**: Factory pattern (model creation), Strategy pattern (device selection), Observer pattern (metrics)
- **Architecture**: Modular design with clear separation between detection, preprocessing, and device management

#### bmm-tea Customization
- **Focus**: Performance regression testing, integration testing, security testing
- **Tools**: pytest, benchmarking frameworks, coverage analysis
- **Specialties**: Edge device testing, real-time performance validation

## Development Workflow

1. **Story Creation** (bmm-pm): Create user stories with acceptance criteria
2. **Development** (bmm-dev): Implement features with comprehensive tests
3. **Code Review** (bmm-dev): Automated review with fixes
4. **Testing** (bmm-tea): Test design, automation, and review
5. **Documentation** (bmm-tech-writer): API docs and guides

## Technology Stack

- **Language**: Python 3.13+
- **Core Libraries**: OpenCV, NumPy, PyTorch
- **Model Formats**: PyTorch (.pt), ONNX (.onnx)
- **Optimization**: ONNX Runtime, quantization (INT8/FP16)
- **Testing**: pytest, coverage, benchmarks
- **CLI**: Custom CLI with argparse
- **Performance**: async/await, threading, multiprocessing

## Quality Standards

- **Code Coverage**: Minimum 80% for new code
- **Performance**: < 30ms inference time on target hardware
- **Testing**: Unit tests for all functions, integration tests for workflows
- **Documentation**: API docs for all public interfaces
- **Security**: No hardcoded credentials, secure model loading