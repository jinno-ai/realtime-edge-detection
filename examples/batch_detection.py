"""
Batch Detection Example

Demonstrates how to use AsyncDetector for efficient batch processing
of multiple images. Batch processing optimizes throughput by processing
images in groups.
"""

import time
from pathlib import Path

import numpy as np
import cv2

from src.api import AsyncDetector, PartialBatchError
from src.detection.yolov8 import YOLOv8Detector


def main():
    """Main batch detection example."""

    print("=" * 70)
    print("Batch Detection Example")
    print("=" * 70)

    # Initialize detector
    print("\n1. Loading detector...")
    base_detector = YOLOv8Detector()
    base_detector.load_model('yolov8n.pt', device='cpu')

    async_detector = AsyncDetector(
        base_detector,
        max_workers=4,
        default_batch_size=8
    )

    # Load sample images
    print("\n2. Loading sample images...")
    image_dir = Path("data/test_images")

    if image_dir.exists():
        image_paths = list(image_dir.glob("*.jpg"))[:20]
        images = [cv2.imread(str(p)) for p in image_paths]
        images = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images]
        print(f"   Loaded {len(images)} images from {image_dir}")
    else:
        print(f"   Creating {20} dummy images for demonstration")
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(20)
        ]

    # Example 1: Basic batch detection
    print("\n" + "-" * 70)
    print("Example 1: Basic Batch Detection")
    print("-" * 70)

    batch_size = 8
    print(f"\nProcessing {len(images)} images with batch size {batch_size}...")

    start = time.time()
    results = async_detector.detect_batch(images, batch_size=batch_size)
    elapsed = time.time() - start

    total_detections = sum(r.metadata['num_detections'] for r in results)
    fps = len(images) / elapsed

    print(f"\nCompleted in {elapsed*1000:.2f}ms")
    print(f"Total detections: {total_detections}")
    print(f"Throughput: {fps:.1f} FPS")
    print(f"Average per image: {elapsed/len(images)*1000:.2f}ms")

    # Example 2: Different batch sizes
    print("\n" + "-" * 70)
    print("Example 2: Comparing Different Batch Sizes")
    print("-" * 70)

    test_images = images[:16]
    batch_sizes = [1, 4, 8, 16]

    print(f"\nProcessing {len(test_images)} images with different batch sizes:")
    print(f"\n{'Batch Size':<12} {'Time (ms)':<12} {'FPS':<10} {'Avg (ms)':<10}")
    print("-" * 50)

    for bs in batch_sizes:
        start = time.time()
        results = async_detector.detect_batch(test_images, batch_size=bs)
        elapsed = time.time() - start

        fps = len(test_images) / elapsed
        avg_ms = elapsed / len(test_images) * 1000

        print(f"{bs:<12} {elapsed*1000:<12.2f} {fps:<10.1f} {avg_ms:<10.2f}")

    # Example 3: Batch detection with error handling
    print("\n" + "-" * 70)
    print("Example 3: Batch Detection with Error Handling")
    print("-" * 70)

    print("\nProcessing with partial batch error handling...")

    try:
        results = async_detector.detect_batch(images[:10], batch_size=4)
        print(f"Success! Processed {len(results)} images")
    except PartialBatchError as e:
        print(f"Partial failure detected:")
        print(f"  Successful: {e.successful}/{e.total}")
        print(f"  Results still available: {len(e.results)}")

        # Access partial results
        for i, result in enumerate(e.results[:3]):
            print(f"    Image {i+1}: {result.metadata['num_detections']} detections")

    # Example 4: Processing in chunks
    print("\n" + "-" * 70)
    print("Example 4: Processing Large Dataset in Chunks")
    print("-" * 70)

    # Simulate large dataset
    large_dataset = images * 5  # 100 images
    chunk_size = 20

    print(f"\nProcessing {len(large_dataset)} images in chunks of {chunk_size}...")

    start = time.time()
    all_results = []

    for i in range(0, len(large_dataset), chunk_size):
        chunk = large_dataset[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        total_chunks = (len(large_dataset) + chunk_size - 1) // chunk_size

        print(f"  Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} images)...")

        chunk_results = async_detector.detect_batch(chunk, batch_size=8)
        all_results.extend(chunk_results)

        # Show progress
        progress = (i + len(chunk)) / len(large_dataset) * 100
        total_dets = sum(r.metadata['num_detections'] for r in all_results)
        print(f"    Progress: {progress:.0f}% | Total detections: {total_dets}")

    elapsed = time.time() - start
    fps = len(all_results) / elapsed

    print(f"\nCompleted!")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Average FPS: {fps:.1f}")
    print(f"  Total detections: {sum(r.metadata['num_detections'] for r in all_results)}")

    # Example 5: Batch statistics
    print("\n" + "-" * 70)
    print("Example 5: Batch Processing Statistics")
    print("-" * 70)

    test_batch = images[:10]

    start = time.time()
    results = async_detector.detect_batch(test_batch, batch_size=5)
    elapsed = time.time() - start

    # Calculate statistics
    detection_counts = [r.metadata['num_detections'] for r in results]
    total_detections = sum(detection_counts)
    avg_detections = total_detections / len(results)
    max_detections = max(detection_counts)
    min_detections = min(detection_counts)

    print(f"\nBatch Statistics:")
    print(f"  Images processed: {len(results)}")
    print(f"  Processing time: {elapsed*1000:.2f}ms")
    print(f"  Throughput: {len(results)/elapsed:.1f} FPS")
    print(f"\nDetection Statistics:")
    print(f"  Total detections: {total_detections}")
    print(f"  Average per image: {avg_detections:.1f}")
    print(f"  Max detections: {max_detections}")
    print(f"  Min detections: {min_detections}")

    # Cleanup
    print("\n" + "-" * 70)
    async_detector.shutdown()
    print("Detector shutdown complete")

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
