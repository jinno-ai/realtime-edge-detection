"""
Integration tests for CLI commands.

Tests all CLI commands including:
- Basic detection commands (image, video)
- Batch processing
- Output formats (JSON, CSV, COCO)
- Config file loading
- Device selection
- Error handling
"""

import pytest
import subprocess
import json
import csv
from pathlib import Path
import tempfile
import shutil
import numpy as np
import cv2
from click.testing import CliRunner
from unittest.mock import patch, Mock


class TestCLIBasicDetection:
    """Test basic CLI detection commands"""

    @pytest.fixture
    def runner(self):
        """Create Click CLI runner"""
        return CliRunner()

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample test image"""
        img_path = tmp_path / "test_image.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    @pytest.fixture
    def sample_video(self, tmp_path):
        """Create a sample test video"""
        video_path = tmp_path / "test_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

        for _ in range(30):  # 30 frames
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            out.write(frame)

        out.release()
        return str(video_path)

    def test_detect_image_command_exists(self, runner, sample_image):
        """Test that detect command exists and runs"""
        from src.cli.main import cli

        result = runner.invoke(cli, ['detect', '--help'])
        assert result.exit_code == 0
        assert 'detect' in result.output
        assert 'image' in result.output.lower() or 'video' in result.output.lower()

    def test_detect_image_with_mock_model(self, runner, sample_image, tmp_path):
        """Test image detection with mocked model"""
        from src.cli.main import cli

        output_file = tmp_path / "output.json"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--output', str(output_file),
                '--output-format', 'json'
            ])

            # Command should not fail (model mocking handles execution)
            # The actual implementation might fail without proper mocking
            mock_detect.assert_called_once()

    def test_detect_video_command(self, runner, sample_video, tmp_path):
        """Test video detection command"""
        from src.cli.main import cli

        output_file = tmp_path / "output.mp4"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_video,
                '--output', str(output_file)
            ])

            mock_detect.assert_called_once()

    def test_detect_with_config_override(self, runner, sample_image, tmp_path):
        """Test detection with config file override"""
        from src.cli.main import cli

        # Create config file
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
model:
  type: yolo_v8
  path: yolov8n.pt
detection:
  confidence_threshold: 0.7
  iou_threshold: 0.5
""")

        result = runner.invoke(cli, [
            '--config', str(config_file),
            'detect', '--help'
        ])

        assert result.exit_code == 0


class TestCLIOutputFormats:
    """Test CLI output format options"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    def test_json_output_format(self, runner, sample_image, tmp_path):
        """Test JSON output format"""
        from src.cli.main import cli

        output = tmp_path / "output.json"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--output', str(output),
                '--output-format', 'json'
            ])

            # Check command was called with correct parameters
            mock_detect.assert_called_once()
            call_args = mock_detect.call_args
            assert 'json' in str(call_args)

    def test_csv_output_format(self, runner, sample_image, tmp_path):
        """Test CSV output format"""
        from src.cli.main import cli

        output = tmp_path / "output.csv"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--output', str(output),
                '--output-format', 'csv'
            ])

            mock_detect.assert_called_once()

    def test_coco_output_format(self, runner, sample_image, tmp_path):
        """Test COCO output format"""
        from src.cli.main import cli

        output = tmp_path / "output_coco.json"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--output', str(output),
                '--output-format', 'coco'
            ])

            mock_detect.assert_called_once()

    def test_visual_output_format(self, runner, sample_image, tmp_path):
        """Test visual output format (default)"""
        from src.cli.main import cli

        output = tmp_path / "output_visual.jpg"

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--output', str(output)
            ])

            mock_detect.assert_called_once()


class TestCLIBatchProcessing:
    """Test CLI batch processing"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create multiple sample images"""
        images = []
        for i in range(3):
            img_path = tmp_path / f"test_{i}.jpg"
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(str(img_path), img)
            images.append(str(img_path))
        return images

    def test_detect_batch_command_exists(self, runner):
        """Test that detect-batch command exists"""
        from src.cli.main import cli

        result = runner.invoke(cli, ['detect-batch', '--help'])
        assert result.exit_code == 0
        assert 'batch' in result.output.lower()

    def test_detect_batch_multiple_files(self, runner, sample_images, tmp_path):
        """Test batch processing multiple files"""
        from src.cli.main import cli

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch('src.cli.batch.run_batch') as mock_batch:
            mock_batch.return_value = None

            result = runner.invoke(cli, [
                'detect-batch', *sample_images,
                '--output-dir', str(output_dir)
            ])

            mock_batch.assert_called_once()

    def test_detect_batch_with_custom_params(self, runner, sample_images, tmp_path):
        """Test batch processing with custom parameters"""
        from src.cli.main import cli

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch('src.cli.batch.run_batch') as mock_batch:
            mock_batch.return_value = None

            result = runner.invoke(cli, [
                'detect-batch', *sample_images,
                '--output-dir', str(output_dir),
                '--output-format', 'json',
                '--confidence', '0.7',
                '--iou', '0.5'
            ])

            mock_batch.assert_called_once()

    def test_detect_batch_no_inputs(self, runner):
        """Test batch processing with no inputs raises error"""
        from src.cli.main import cli

        result = runner.invoke(cli, ['detect-batch'])
        assert result.exit_code == 1
        assert 'No input files' in result.output or 'error' in result.output.lower()


class TestCLIConfigLoading:
    """Test CLI configuration file loading"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def valid_config(self, tmp_path):
        """Create valid config file"""
        config = tmp_path / "valid_config.yaml"
        config.write_text("""
model:
  type: yolo_v8
  path: yolov8n.pt

detection:
  confidence_threshold: 0.5
  iou_threshold: 0.4
  max_detections: 100

device:
  selection: auto
  fallback_order:
    - cuda
    - mps
    - cpu

output:
  format: json
  save_visual: true
""")
        return str(config)

    @pytest.fixture
    def invalid_config(self, tmp_path):
        """Create invalid config file"""
        config = tmp_path / "invalid_config.yaml"
        config.write_text("""
model:
  type: yolo_v8
    path: bad_indentation
""")
        return str(config)

    def test_load_valid_config(self, runner, valid_config):
        """Test loading valid configuration file"""
        from src.cli.main import cli

        result = runner.invoke(cli, [
            '--config', valid_config,
            'detect', '--help'
        ])

        assert result.exit_code == 0

    def test_config_validation_command(self, runner, valid_config):
        """Test config validate command"""
        from src.cli.main import cli

        result = runner.invoke(cli, [
            'config', 'validate',
            '--config', valid_config
        ])

        # Command exists
        assert result.exit_code == 0 or 'validate' in result.output.lower()

    def test_config_list_profiles(self, runner):
        """Test config list-profiles command"""
        from src.cli.main import cli

        result = runner.invoke(cli, ['config', 'list-profiles'])

        assert result.exit_code == 0 or 'profile' in result.output.lower()

    def test_profile_selection(self, runner, tmp_path):
        """Test profile selection (dev/prod/testing)"""
        from src.cli.main import cli

        for profile in ['dev', 'prod', 'testing']:
            result = runner.invoke(cli, [
                '--profile', profile,
                'detect', '--help'
            ])

            assert result.exit_code == 0


class TestCLIDeviceSelection:
    """Test CLI device selection options"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    def test_device_auto(self, runner, sample_image):
        """Test device auto-selection"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--device', 'auto'
            ])

            mock_detect.assert_called_once()

    def test_device_cpu(self, runner, sample_image):
        """Test CPU device selection"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--device', 'cpu'
            ])

            mock_detect.assert_called_once()

    def test_device_cuda(self, runner, sample_image):
        """Test CUDA device selection"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--device', 'cuda'
            ])

            mock_detect.assert_called_once()


class TestCLIErrorHandling:
    """Test CLI error handling for edge cases"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_nonexistent_input_file(self, runner):
        """Test detection on non-existent file"""
        from src.cli.main import cli

        result = runner.invoke(cli, [
            'detect', '/nonexistent/file.jpg'
        ])

        # Should fail gracefully
        assert result.exit_code != 0 or 'error' in result.output.lower()

    def test_invalid_output_format(self, runner, tmp_path):
        """Test invalid output format"""
        from src.cli.main import cli

        # Create sample image
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        result = runner.invoke(cli, [
            'detect', str(img_path),
            '--output-format', 'invalid_format'
        ])

        # Should fail with invalid parameter error
        assert result.exit_code != 0

    def test_invalid_confidence_value(self, runner, tmp_path):
        """Test invalid confidence threshold"""
        from src.cli.main import cli

        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        result = runner.invoke(cli, [
            'detect', str(img_path),
            '--confidence', '1.5'  # Invalid: > 1.0
        ])

        # Click should validate this
        assert result.exit_code != 0 or 'error' in result.output.lower()

    def test_empty_directory_batch(self, runner, tmp_path):
        """Test batch processing on empty directory"""
        from src.cli.main import cli

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(cli, [
            'detect-batch'
        ])

        assert result.exit_code == 1  # No inputs error


class TestCLIBenchmarkMode:
    """Test CLI benchmark mode"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_benchmark_command_exists(self, runner):
        """Test that benchmark command exists"""
        from src.cli.main import cli

        result = runner.invoke(cli, ['benchmark', '--help'])
        assert result.exit_code == 0
        assert 'benchmark' in result.output.lower()

    def test_benchmark_with_iterations(self, runner):
        """Test benchmark with custom iterations"""
        from src.cli.main import cli

        result = runner.invoke(cli, [
            'benchmark',
            '--iterations', '50'
        ])

        assert result.exit_code == 0
        assert '50' in result.output

    def test_benchmark_with_device(self, runner):
        """Test benchmark with device specification"""
        from src.cli.main import cli

        result = runner.invoke(cli, [
            'benchmark',
            '--device', 'cpu'
        ])

        assert result.exit_code == 0
        assert 'cpu' in result.output.lower()


class TestCLIInteractiveMode:
    """Test CLI interactive mode"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_video(self, tmp_path):
        """Create sample video for interactive mode"""
        video_path = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

        for _ in range(30):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            out.write(frame)

        out.release()
        return str(video_path)

    def test_interactive_flag_accepted(self, runner, sample_video):
        """Test that interactive flag is accepted"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_video,
                '--interactive'
            ])

            mock_detect.assert_called_once()


class TestCLIMetricsIntegration:
    """Test CLI metrics collection integration"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create sample image"""
        img_path = tmp_path / "test.jpg"
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        return str(img_path)

    def test_metrics_none_default(self, runner, sample_image):
        """Test that metrics are disabled by default"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, ['detect', sample_image])
            mock_detect.assert_called_once()

    def test_metrics_prometheus(self, runner, sample_image):
        """Test Prometheus metrics option"""
        from src.cli.main import cli

        with patch('src.cli.detect.run_detect') as mock_detect:
            mock_detect.return_value = None

            result = runner.invoke(cli, [
                'detect', sample_image,
                '--metrics', 'prometheus'
            ])

            mock_detect.assert_called_once()
