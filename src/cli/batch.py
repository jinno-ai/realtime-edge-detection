"""
Batch processing module for multiple input files.

This module handles batch processing of multiple images or videos with
progress tracking and summary statistics.
"""

import click
from pathlib import Path
from typing import List
from tqdm import tqdm

from src.cli.detect import create_detector, process_image, process_video
from src.cli.output import OutputHandler


def run_batch(ctx, inputs: List[str], output_dir: str, output_format: str,
              confidence=None, iou=None, device=None):
    """
    Run detection on multiple files in batch mode.

    Args:
        ctx: Click context
        inputs: List of input file paths
        output_dir: Output directory path
        output_format: Output format
        confidence: Override confidence threshold
        iou: Override IOU threshold
        device: Override device selection
    """
    from ultralytics import YOLO

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize detector (shared across all files)
    click.echo("Initializing detector...")
    config_mgr, model_path, selected_device = create_detector(
        ctx, None, confidence, iou, device
    )

    detector = YOLO(str(model_path))
    device_name = selected_device.replace('cuda', 'cuda:0')
    detector.to(device_name)

    # Process files
    results_summary = {
        'total_files': len(inputs),
        'successful': 0,
        'failed': 0,
        'total_detections': 0,
        'failed_files': []
    }

    click.echo(f"\nProcessing {len(inputs)} files...")

    for input_file in tqdm(inputs, desc="Batch progress"):
        input_path = Path(input_file)

        try:
            # Process based on file type
            if input_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                # Image
                result = process_image(detector, input_path, None)
                detections = result['detections']
            elif input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                # Video
                result = process_video(detector, input_path, None)
                detections = result['detections']
            else:
                click.echo(f"\nSkipping unsupported file: {input_file}")
                results_summary['failed'] += 1
                results_summary['failed_files'].append(str(input_file))
                continue

            # Generate output path
            output_file = output_path / f"{input_path.stem}_detections"
            if output_format == 'visual':
                output_file = output_file.with_suffix('.jpg')
            elif output_format == 'json':
                output_file = output_file.with_suffix('.json')
            elif output_format == 'csv':
                output_file = output_file.with_suffix('.csv')
            elif output_format == 'coco':
                output_file = output_file.with_suffix('.json')

            # Save results
            if output_format == 'visual' and 'image' in result:
                OutputHandler.to_visual(result['image'], detections, output_file)
            elif output_format == 'json':
                metadata = {
                    'input_file': str(input_path),
                    'model': str(model_path),
                    'device': selected_device
                }
                OutputHandler.to_json(detections, metadata, output_file)
            elif output_format == 'csv':
                OutputHandler.to_csv(detections, output_file)
            elif output_format == 'coco':
                image_info = {
                    'filename': input_path.name,
                    'width': result.get('image', ...).shape[1] if 'image' in result else 0,
                    'height': result.get('image', ...).shape[0] if 'image' in result else 0
                }
                OutputHandler.to_coco(detections, image_info, output_file)

            results_summary['successful'] += 1
            results_summary['total_detections'] += len(detections)

        except Exception as e:
            click.echo(f"\nError processing {input_file}: {e}", err=True)
            results_summary['failed'] += 1
            results_summary['failed_files'].append(str(input_file))
            continue

    # Print summary
    click.echo(f"\n{'='*60}")
    click.echo("Batch Processing Summary")
    click.echo(f"{'='*60}")
    click.echo(f"Total files:        {results_summary['total_files']}")
    click.echo(f"Successful:         {results_summary['successful']}")
    click.echo(f"Failed:             {results_summary['failed']}")
    click.echo(f"Total detections:   {results_summary['total_detections']}")
    click.echo(f"Output directory:   {output_dir}")

    if results_summary['failed_files']:
        click.echo(f"\nFailed files:")
        for failed_file in results_summary['failed_files']:
            click.echo(f"  - {failed_file}")

    click.echo(f"{'='*60}")
