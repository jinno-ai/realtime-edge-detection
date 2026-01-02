# Realtime Edge Detection - Project Knowledge Index

**Generated:** 2026-01-03
**Documentation Mode:** Initial Scan
**Project Type:** Python Backend / Computer Vision

---

## Quick Start

This index provides navigation to all project documentation and knowledge artifacts for the Realtime Edge Detection project.

**📖 Project Overview:** Computer vision project for real-time object detection on edge devices using YOLO models.

---

## Documentation Sections

### 1. [Project Documentation](project-documentation.md)
**Complete reference documentation for the project**

**Contents:**
- Project Overview & Purpose
- Technology Stack
- Project Structure
- Architecture Patterns
- API Reference
- Configuration Guide
- Testing Strategy
- Development Guidelines
- Performance Optimization
- Deployment Guide
- Troubleshooting

**Use when:** You need comprehensive information about the project structure, APIs, or development workflow.

---

### 2. Test Architecture Documents

#### [Automation Summary](../output/automation-summary.md)
**Test automation expansion results**

- 67 new tests created (55 unit + 12 integration)
- Test infrastructure (fixtures, factories)
- Coverage increased from 27% to 42%
- Test execution results

**Use when:** Understanding test coverage and automation status.

#### [Traceability Matrix](../output/traceability-matrix.md)
**Requirements-to-tests traceability and quality gate decision**

- Coverage analysis by priority (P0/P1/P2/P3)
- Gap analysis with recommendations
- Quality gate decision: ⚠️ CONCERNS
- Test execution evidence

**Use when:** Evaluating deployment readiness and test completeness.

#### [Test Review](../output/test-review.md)
**Comprehensive test quality review**

- Quality score: 88/100 (A - Good)
- Best practices found
- Critical issues and recommendations
- Fixture and factory patterns

**Use when:** Improving test quality or understanding test architecture.

---

### 3. Planning Artifacts

#### [PRD - Product Requirements Document](../output/planning-artifacts/02-PRD.md)
**Product vision and requirements**

**Use when:** Understanding product goals and success criteria.

#### [Architecture Document](../output/planning-artifacts/03-ARCHITECTURE.md)
**Technical architecture and design decisions**

**Use when:** Understanding system design and technical approach.

#### [Epics](../output/planning-artifacts/epics.md)
**Feature breakdown by epic**

**Use when:** Planning features and understanding roadmap.

#### [Analysis](../output/planning-artifacts/01-ANALYSIS.md)
**Project analysis and assessment**

**Use when:** Understanding project context and constraints.

---

## Project Statistics

**Codebase:**
- **Language:** Python 3.14+
- **Source Files:** 11 Python modules
- **Total Lines:** ~2,000+ lines of code
- **Test Coverage:** 42% (395/681 lines)
- **Test Count:** 67 tests (55 unit + 12 integration)

**Key Modules:**
- `src/config/config_manager.py` - Hierarchical configuration
- `src/models/yolo_detector.py` - YOLO detection engine
- `src/preprocessing/image_processor.py` - Image processing pipeline
- `src/utils/video_utils.py` - Video processing utilities

---

## How to Use This Documentation

### For New Developers

1. **Start here:** [Project Documentation](project-documentation.md)
   - Read "Project Overview" and "Architecture Patterns"
   - Review "Development Guidelines"

2. **Understand testing:** [Test Review](../output/test-review.md)
   - Review "Best Practices Found"
   - Study "Fixture Architecture"

3. **Run the code:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Run tests
   pytest tests/ -v

   # Run detection example
   python -c "from src.models.yolo_detector import YOLODetector; detector = YOLODetector(); print('Ready!')"
   ```

### For AI Assistants

**When assisting with development:**

1. **Load project context:**
   - Read [Project Documentation](project-documentation.md) for architecture
   - Check [Test Review](../output/test-review.md) for test patterns
   - Review [Automation Summary](../output/automation-summary.md) for coverage gaps

2. **Follow conventions:**
   - Use factories from `tests/factories/__init__.py` for test data
   - Use fixtures from `tests/conftest.py` for common test setup
   - Follow naming conventions from "Development Guidelines"

3. **Check test status:**
   - Coverage: 42% (needs improvement in ConfigManager, YOLODetector)
   - Integration tests: Need mock fixes (12 tests failing)
   - Test quality: 88/100 (Good, but needs test IDs)

### For Code Reviewers

1. **Review against standards:**
   - Check [Test Review](../output/test-review.md) quality criteria
   - Verify [Automation Summary](../output/automation-summary.md) recommendations
   - Ensure [Traceability Matrix](../output/traceability-matrix.md) coverage

2. **Key quality gates:**
   - P0 coverage: 100% ✅
   - P1 coverage: 87% ⚠️ (below 90% threshold)
   - Test pass rate: 82% ⚠️ (mock issues)

---

## Workflow Artifacts

### BMad Framework Documentation

This project uses the BMad (Business Model & Architecture Development) framework for AI-assisted development.

**Key BMad Components:**
- `_bmad/core/` - Core workflow engine
- `_bmad/bmm/` - Business Model & workflows
- `_bmad/output/` - Generated artifacts

**Workflows Used:**
1. **document-project** - This workflow, generates project documentation
2. **testarch-automate** - Test automation expansion
3. **testarch-trace** - Requirements traceability
4. **testarch-test-review** - Test quality review

---

## Quick Reference

### Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_image_processor.py -v

# Run by marker
pytest -m unit -v
pytest -m integration -v

# Check coverage
pytest --cov=src --cov-report=term-missing
```

### Key Files

**Configuration:**
- `requirements.txt` - Python dependencies
- `pytest.ini` - Test configuration
- `config.yaml` - Detection configuration (user-provided)

**Source Code:**
- `src/config/config_manager.py` - Configuration management
- `src/models/yolo_detector.py` - Detection engine
- `src/preprocessing/image_processor.py` - Preprocessing
- `src/utils/video_utils.py` - Video utilities

**Tests:**
- `tests/conftest.py` - Shared fixtures
- `tests/factories/__init__.py` - Test data factories
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests

---

## Documentation Maintenance

**Last Generated:** 2026-01-03
**Version:** 1.0
**Workflow:** document-project (initial_scan)

**When to update:**
- After major architecture changes
- When adding new modules or features
- After test coverage significantly changes
- When deployment requirements change

**How to regenerate:**
```bash
/bmad:bmm:workflows:document-project
```

---

## Support & Contributing

**Project Status:** Active Development

**For questions:**
1. Check [Troubleshooting](project-documentation.md#troubleshooting) section
2. Review [Test Review](../output/test-review.md) for known issues
3. Consult [Traceability Matrix](../output/traceability-matrix.md) for gaps

**Contributing:**
1. Follow [Development Guidelines](project-documentation.md#development-guidelines)
2. Add tests for new features
3. Update documentation as needed
4. Ensure test coverage doesn't decrease

---

**Index Version:** 1.0
**Documentation Status:** Complete ✅
**Next Review:** After major feature additions

<!-- Powered by BMAD-CORE™ -->
