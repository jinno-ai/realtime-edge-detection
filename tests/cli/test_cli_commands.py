"""
Unit tests for CLI commands.

Tests CLI argument parsing, command execution, and integration with
configuration/model/device managers.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from src.cli.main import cli


class TestCLICommands:
    """Test CLI command parsing and basic functionality."""

    def test_cli_main_command(self):
        """Test main CLI command exists and shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Real-time Edge Detection CLI' in result.output
        assert 'detect' in result.output

    def test_detect_command_help(self):
        """Test detect command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['detect', '--help'])
        assert result.exit_code == 0
        assert 'INPUT' in result.output
        assert '--output' in result.output
        assert '--output-format' in result.output
        assert '--interactive' in result.output

    def test_detect_batch_command_help(self):
        """Test detect-batch command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['detect-batch', '--help'])
        assert result.exit_code == 0
        assert 'INPUTS' in result.output
        assert '--output-dir' in result.output

    def test_config_command_help(self):
        """Test config command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'validate' in result.output
        assert 'show' in result.output
        assert 'list-profiles' in result.output


class TestCLIMetrics:
    """Test metrics tracking functionality."""

    def test_metrics_tracker_initialization(self):
        """Test MetricsTracker initialization."""
        from src.cli.metrics import MetricsTracker

        tracker = MetricsTracker()
        assert tracker.start_time is None
        assert tracker.inference_times == []
        assert tracker.detection_counts == []

    def test_metrics_tracker_inference(self):
        """Test inference timing."""
        from src.cli.metrics import MetricsTracker
        import time

        tracker = MetricsTracker()
        tracker.start_inference()
        time.sleep(0.01)  # 10ms
        elapsed = tracker.end_inference(detection_count=5)

        assert elapsed > 0
        assert elapsed < 1.0  # Should be around 10ms
        assert len(tracker.inference_times) == 1
        assert tracker.detection_counts == [5]

    def test_metrics_tracker_stats(self):
        """Test statistics calculation."""
        from src.cli.metrics import MetricsTracker

        tracker = MetricsTracker()
        tracker.inference_times = [0.025, 0.030, 0.020]  # 25ms, 30ms, 20ms
        tracker.detection_counts = [3, 4, 2]

        stats = tracker.get_stats()
        assert stats['total_inferences'] == 3
        assert stats['detection_count'] == 9
        assert 24.9 < stats['avg_inference_time_ms'] <= 25.0  # Average of 25, 30, 20
        assert 30 < stats['fps'] < 50  # FPS around 40

    def test_metrics_tracker_format(self):
        """Test stats formatting."""
        from src.cli.metrics import MetricsTracker

        tracker = MetricsTracker()
        tracker.inference_times = [0.025]
        tracker.detection_counts = [5]

        stats = tracker.get_stats()
        formatted = tracker.format_stats(stats)

        assert 'Detected 5 objects' in formatted
        assert '25.0ms' in formatted
        assert 'FPS' in formatted

    def test_metrics_tracker_reset(self):
        """Test metrics reset."""
        from src.cli.metrics import MetricsTracker

        tracker = MetricsTracker()
        tracker.inference_times = [0.025]
        tracker.detection_counts = [5]

        tracker.reset()
        assert tracker.inference_times == []
        assert tracker.detection_counts == []


class TestOutputFormats:
    """Test output format handlers."""

    def test_json_output(self, tmp_path):
        """Test JSON output format."""
        from src.cli.output import OutputHandler

        detections = [
            {
                'bbox': [10, 20, 30, 40],
                'confidence': 0.95,
                'class_id': 0,
                'class_name': 'person'
            }
        ]
        metadata = {'model': 'yolov8n.pt', 'device': 'cpu'}
        output_path = tmp_path / 'test.json'

        OutputHandler.to_json(detections, metadata, output_path)

        assert output_path.exists()
        import json
        with open(output_path) as f:
            data = json.load(f)
        assert data['total_detections'] == 1
        assert data['detections'][0]['class_name'] == 'person'
        assert 'timestamp' in data

    def test_csv_output(self, tmp_path):
        """Test CSV output format."""
        from src.cli.output import OutputHandler

        detections = [
            {
                'bbox': [10.5, 20.5, 30.5, 40.5],
                'confidence': 0.95,
                'class_id': 0,
                'class_name': 'person'
            }
        ]
        output_path = tmp_path / 'test.csv'

        OutputHandler.to_csv(detections, output_path)

        assert output_path.exists()
        import csv
        with open(output_path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # Header + 1 data row
        assert rows[0][0] == 'class'
        assert rows[1][0] == 'person'

    def test_visual_output(self, tmp_path):
        """Test visual output format."""
        from src.cli.output import OutputHandler
        import numpy as np

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = [
            {
                'bbox': [10, 20, 30, 40],
                'confidence': 0.95,
                'class_id': 0,
                'class_name': 'person'
            }
        ]
        output_path = tmp_path / 'test.jpg'

        OutputHandler.to_visual(image, detections, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_draw_detections(self):
        """Test drawing detections on image."""
        from src.cli.output import OutputHandler
        import numpy as np

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = [
            {
                'bbox': [10, 20, 30, 40],
                'confidence': 0.95,
                'class_id': 0,
                'class_name': 'person'
            }
        ]

        annotated = OutputHandler.draw_detections(image, detections)

        assert annotated.shape == image.shape
        # Annotated image should be different from original
        assert not np.array_equal(annotated, image)

    def test_class_colors(self):
        """Test color mapping for classes."""
        from src.cli.output import OutputHandler

        color_person = OutputHandler.get_color('person')
        color_car = OutputHandler.get_color('car')
        color_unknown = OutputHandler.get_color('unknown')

        assert color_person == (0, 255, 0)  # Green
        assert color_car == (255, 0, 0)  # Blue
        assert color_unknown == (128, 128, 128)  # Gray (default)


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    import numpy as np
    import cv2

    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    image_path = tmp_path / "test.jpg"
    cv2.imwrite(str(image_path), image)
    return image_path


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_nonexistent_input_file(self):
        """Test error handling for nonexistent input."""
        runner = CliRunner()
        result = runner.invoke(cli, ['detect', 'nonexistent.jpg'])
        assert result.exit_code != 0

    def test_invalid_output_format(self, sample_image):
        """Test error on invalid output format."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'detect',
            str(sample_image),
            '--output-format', 'invalid'
        ])
        assert result.exit_code != 0
