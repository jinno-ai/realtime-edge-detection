"""
Main CLI entry point for real-time edge detection.

This module provides the Click-based command-line interface with support for
configuration management, device selection, and various output formats.
"""

import click
import sys
from pathlib import Path
from typing import Optional


@click.group()
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--profile', type=click.Choice(['dev', 'prod', 'testing'], case_sensitive=False),
              help='Configuration profile (dev/prod/testing)')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, profile, verbose):
    """
    Real-time Edge Detection CLI

    Perform real-time object detection on images and videos using YOLO models.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['profile'] = profile
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('input', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--output-format', type=click.Choice(['json', 'csv', 'coco', 'visual'],
                                                   case_sensitive=False),
              default='visual', help='Output format (json/csv/coco/visual)')
@click.option('--interactive', is_flag=True, help='Interactive mode with real-time preview')
@click.option('--model', type=click.Path(), help='Override model path')
@click.option('--confidence', type=float, help='Override confidence threshold (0.0-1.0)')
@click.option('--iou', type=float, help='Override IOU threshold (0.0-1.0)')
@click.option('--device', type=str, help='Override device selection (auto/cpu/cuda/mps)')
@click.option('--batch', is_flag=True, help='Batch processing mode for multiple inputs')
@click.option('--benchmark', is_flag=True, help='Benchmark mode for performance testing')
@click.pass_context
def detect(ctx, input, output, output_format, interactive, model, confidence, iou, device, batch, benchmark):
    """
    Run object detection on image or video.

    Examples:

        # Basic detection on image
        edge-detection detect image.jpg

        # Interactive mode with real-time preview
        edge-detection detect video.mp4 --interactive

        # Export results to JSON
        edge-detection detect image.jpg --output results.json --output-format json

        # Batch processing with custom confidence
        edge-detection detect *.jpg --confidence 0.7 --batch
    """
    from src.cli.detect import run_detect

    # Run detection
    run_detect(
        ctx, input, output, output_format, interactive,
        model, confidence, iou, device, batch, benchmark
    )


@cli.command()
@click.argument('inputs', nargs=-1, type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), default='./output',
              help='Output directory for batch results')
@click.option('--output-format', type=click.Choice(['json', 'csv', 'coco', 'visual'],
                                                   case_sensitive=False),
              default='visual', help='Output format')
@click.option('--confidence', type=float, help='Confidence threshold')
@click.option('--iou', type=float, help='IOU threshold')
@click.option('--device', type=str, help='Device selection')
@click.pass_context
def detect_batch(ctx, inputs, output_dir, output_format, confidence, iou, device):
    """
    Run detection on multiple files in batch mode.

    Examples:

        # Process all images in directory
        edge-detection detect-batch *.jpg

        # Batch processing with JSON output
        edge-detection detect-batch *.jpg --output-dir results --output-format json
    """
    from src.cli.batch import run_batch

    if not inputs:
        click.echo("Error: No input files specified", err=True)
        raise SystemExit(1)

    run_batch(
        ctx, list(inputs), output_dir, output_format,
        confidence, iou, device
    )


@cli.command()
@click.option('--model', type=click.Path(), help='Model path for benchmarking')
@click.option('--device', type=str, help='Device to benchmark')
@click.option('--iterations', type=int, default=100, help='Number of benchmark iterations')
@click.pass_context
def benchmark(ctx, model, device, iterations):
    """
    Run performance benchmarks.

    Measure inference speed, memory usage, and throughput.

    Example:

        # Run default benchmark
        edge-detection benchmark

        # Benchmark specific device
        edge-detection benchmark --device cuda --iterations 200
    """
    click.echo("Benchmark mode - Coming soon!")
    click.echo(f"  Model: {model or 'default'}")
    click.echo(f"  Device: {device or 'auto'}")
    click.echo(f"  Iterations: {iterations}")


@cli.command()
@click.argument('action', type=click.Choice(['validate', 'show', 'list-profiles']))
@click.option('--config', type=click.Path(exists=True), help='Config file to validate')
@click.pass_context
def config_cmd(ctx, action, config):
    """
    Configuration management commands.

    Actions:

        validate: Validate configuration file
        show: Show current configuration
        list-profiles: List available configuration profiles

    Examples:

        # Validate configuration
        edge-detection config validate --config config.yaml

        # List available profiles
        edge-detection config list-profiles
    """
    from src.cli.detect import handle_config_command

    handle_config_command(action, config)


if __name__ == '__main__':
    cli()
