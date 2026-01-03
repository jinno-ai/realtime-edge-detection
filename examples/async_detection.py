"""
Async Detection Example

Demonstrates how to use AsyncDetector for non-blocking, parallel detection
on multiple images. This is useful for scenarios where you want to process
multiple images concurrently without blocking the main thread.
"""

import asyncio
import time
from pathlib import Path

import numpy as np
import cv2

from src.api import AsyncDetector
from src.detection.yolov8 import YOLOv8Detector


async def main():
    """Main async detection example."""

    print("=" * 70)
    print("Async Detection Example")
    print("=" * 70)

    # Initialize base detector
    print("\n1. Loading base detector...")
    base_detector = YOLOv8Detector()
    base_detector.load_model('yolov8n.pt', device='cpu')

    # Wrap with async interface
    print("2. Creating AsyncDetector with 4 workers...")
    async_detector = AsyncDetector(
        base_detector,
        max_workers=4,
        default_batch_size=8
    )

    # Load sample images
    print("\n3. Loading sample images...")
    image_dir = Path("data/test_images")

    if image_dir.exists():
        # Load real images
        image_paths = list(image_dir.glob("*.jpg"))[:5]
        images = [cv2.imread(str(p)) for p in image_paths]
        images = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images]
        print(f"   Loaded {len(images)} images from {image_dir}")
    else:
        # Create dummy images for demonstration
        print(f"   Creating {5} dummy images for demonstration")
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(5)
        ]

    # Example 1: Single async detection
    print("\n" + "-" * 70)
    print("Example 1: Single Async Detection")
    print("-" * 70)

    start = time.time()
    result = await async_detector.detect_async(images[0])
    elapsed = time.time() - start

    print(f"\nDetection completed in {elapsed*1000:.2f}ms")
    print(f"Detected {result.metadata['num_detections']} objects")
    if result.metadata['num_detections'] > 0:
        print(f"  Boxes: {result.boxes.shape}")
        print(f"  Scores: {result.scores.shape}")
        print(f"  Classes: {result.classes.shape}")

    # Example 2: Concurrent detections
    print("\n" + "-" * 70)
    print("Example 2: Concurrent Detections")
    print("-" * 70)

    print(f"\nProcessing {len(images)} images concurrently...")

    start = time.time()

    # Submit all detections concurrently
    tasks = [async_detector.detect_async(img) for img in images]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start
    fps = len(images) / elapsed

    print(f"\nCompleted in {elapsed*1000:.2f}ms")
    print(f"Throughput: {fps:.1f} FPS")
    print(f"\nResults:")
    for i, result in enumerate(results):
        print(f"  Image {i+1}: {result.metadata['num_detections']} detections")

    # Example 3: Async detection with error handling
    print("\n" + "-" * 70)
    print("Example 3: Async Detection with Error Handling")
    print("-" * 70)

    async def detect_with_retries(detector, image, max_retries=3):
        """Detect with retries on failure."""
        for attempt in range(max_retries):
            try:
                result = await detector.detect_async(image)
                return result, None
            except Exception as e:
                if attempt == max_retries - 1:
                    return None, str(e)
                await asyncio.sleep(0.1)  # Brief delay before retry

    print("\nRunning detection with retry logic...")
    result, error = await detect_with_retries(async_detector, images[0])

    if error:
        print(f"  Detection failed after retries: {error}")
    else:
        print(f"  Detection succeeded: {result.metadata['num_detections']} objects")

    # Example 4: Processing with progress tracking
    print("\n" + "-" * 70)
    print("Example 4: Processing with Progress Tracking")
    print("-" * 70)

    async def detect_with_progress(detector, images):
        """Detect with progress updates."""
        total = len(images)
        results = []

        for i, img in enumerate(images, 1):
            result = await detector.detect_async(img)
            results.append(result)

            # Show progress
            progress = (i / total) * 100
            print(f"  Progress: {i}/{total} ({progress:.0f}%) - {result.metadata['num_detections']} detections")

        return results

    print("\nProcessing images with progress tracking...")
    await detect_with_progress(async_detector, images[:3])

    # Example 5: Comparing async vs sequential
    print("\n" + "-" * 70)
    print("Example 5: Performance Comparison")
    print("-" * 70)

    test_images = images[:3]

    # Sequential processing
    print("\nSequential processing:")
    start = time.time()
    sequential_results = [async_detector._detect_sync(img) for img in test_images]
    sequential_time = time.time() - start

    # Async processing
    print("Async processing:")
    start = time.time()
    async_results = await asyncio.gather(*[
        async_detector.detect_async(img) for img in test_images
    ])
    async_time = time.time() - start

    print(f"\nResults:")
    print(f"  Sequential: {sequential_time*1000:.2f}ms")
    print(f"  Async:      {async_time*1000:.2f}ms")
    print(f"  Speedup:    {sequential_time/async_time:.2f}x")

    # Cleanup
    print("\n" + "-" * 70)
    print("Cleaning up...")
    async_detector.shutdown()
    print("Done!")

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
