"""
Performance Benchmarks for AsyncDetector

Comprehensive benchmark suite to measure and compare performance of:
- Synchronous detection
- Async detection
- Batch detection
- Video streaming scenarios
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from src.api import AsyncDetector
from src.detection.yolov8 import YOLOv8Detector


class BenchmarkResults:
    """Store and display benchmark results."""

    def __init__(self, name: str):
        self.name = name
        self.timings: List[float] = []
        self.throughputs: List[float] = []

    def add_result(self, elapsed_time: float, num_items: int):
        """Add a benchmark result."""
        self.timings.append(elapsed_time)
        self.throughputs.append(num_items / elapsed_time if elapsed_time > 0 else 0)

    def get_stats(self) -> Dict[str, float]:
        """Get statistics."""
        return {
            'avg_time': np.mean(self.timings),
            'min_time': np.min(self.timings),
            'max_time': np.max(self.timings),
            'std_time': np.std(self.timings),
            'avg_throughput': np.mean(self.throughputs),
            'max_throughput': np.max(self.throughputs)
        }

    def print_summary(self):
        """Print benchmark summary."""
        stats = self.get_stats()

        print(f"\n{self.name}:")
        print(f"  Average time:     {stats['avg_time']*1000:.2f}ms")
        print(f"  Min time:         {stats['min_time']*1000:.2f}ms")
        print(f"  Max time:         {stats['max_time']*1000:.2f}ms")
        print(f"  Std dev:          {stats['std_time']*1000:.2f}ms")
        print(f"  Avg throughput:   {stats['avg_throughput']:.1f} items/sec")
        print(f"  Max throughput:   {stats['max_throughput']:.1f} items/sec")


def create_test_images(num_images: int, size: Tuple[int, int] = (480, 640, 3)) -> List[np.ndarray]:
    """Create test images."""
    return [np.random.randint(0, 255, size, dtype=np.uint8) for _ in range(num_images)]


def benchmark_sync_detection(detector: AsyncDetector, images: List[np.ndarray], iterations: int = 5) -> BenchmarkResults:
    """Benchmark synchronous detection."""
    print(f"\n{'='*70}")
    print("Benchmark: Synchronous Detection")
    print(f"{'='*70}")

    results = BenchmarkResults("Synchronous Detection")

    for i in range(iterations):
        start = time.time()
        _ = [detector._detect_sync(img) for img in images]
        elapsed = time.time() - start

        results.add_result(elapsed, len(images))
        print(f"  Iteration {i+1}/{iterations}: {elapsed*1000:.2f}ms ({len(images)/elapsed:.1f} FPS)")

    results.print_summary()
    return results


async def benchmark_async_detection(detector: AsyncDetector, images: List[np.ndarray], iterations: int = 5) -> BenchmarkResults:
    """Benchmark async detection."""
    print(f"\n{'='*70}")
    print("Benchmark: Async Detection")
    print(f"{'='*70}")

    results = BenchmarkResults("Async Detection")

    for i in range(iterations):
        start = time.time()
        _ = await asyncio.gather(*[detector.detect_async(img) for img in images])
        elapsed = time.time() - start

        results.add_result(elapsed, len(images))
        print(f"  Iteration {i+1}/{iterations}: {elapsed*1000:.2f}ms ({len(images)/elapsed:.1f} FPS)")

    results.print_summary()
    return results


def benchmark_batch_detection(detector: AsyncDetector, images: List[np.ndarray], batch_sizes: List[int], iterations: int = 3) -> Dict[int, BenchmarkResults]:
    """Benchmark batch detection with different batch sizes."""
    print(f"\n{'='*70}")
    print("Benchmark: Batch Detection")
    print(f"{'='*70}")

    all_results = {}

    for batch_size in batch_sizes:
        print(f"\nBatch size: {batch_size}")
        results = BenchmarkResults(f"Batch Detection (size={batch_size})")

        for i in range(iterations):
            start = time.time()
            _ = detector.detect_batch(images, batch_size=batch_size)
            elapsed = time.time() - start

            results.add_result(elapsed, len(images))
            print(f"  Iteration {i+1}/{iterations}: {elapsed*1000:.2f}ms ({len(images)/elapsed:.1f} FPS)")

        results.print_summary()
        all_results[batch_size] = results

    return all_results


async def benchmark_concurrent_load(detector: AsyncDetector, num_images: int, num_workers_list: List[int]) -> Dict[int, BenchmarkResults]:
    """Benchmark concurrent processing with different worker counts."""
    print(f"\n{'='*70}")
    print("Benchmark: Concurrent Load (Different Worker Counts)")
    print(f"{'='*70}")

    images = create_test_images(num_images)
    all_results = {}

    for num_workers in num_workers_list:
        print(f"\nWorkers: {num_workers}")

        # Create new detector with specific worker count
        temp_detector = AsyncDetector(detector.detector, max_workers=num_workers)

        results = BenchmarkResults(f"Concurrent Load (workers={num_workers})")

        # Run multiple iterations
        for i in range(3):
            start = time.time()
            _ = await asyncio.gather(*[temp_detector.detect_async(img) for img in images])
            elapsed = time.time() - start

            results.add_result(elapsed, len(images))
            print(f"  Iteration {i+1}/3: {elapsed*1000:.2f}ms ({len(images)/elapsed:.1f} FPS)")

        results.print_summary()
        all_results[num_workers] = results

        temp_detector.shutdown()

    return all_results


async def benchmark_video_streaming(detector: AsyncDetector, num_frames: int = 100) -> BenchmarkResults:
    """Benchmark video streaming performance."""
    print(f"\n{'='*70}")
    print("Benchmark: Video Streaming")
    print(f"{'='*70}")

    results = BenchmarkResults("Video Streaming")

    print(f"\nProcessing {num_frames} frames...")

    frame_times = []
    for i in range(num_frames):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        start = time.time()
        _ = await detector.detect_async(frame)
        elapsed = time.time() - start

        frame_times.append(elapsed)

        if (i + 1) % 20 == 0:
            avg_time = np.mean(frame_times[-20:])
            fps = 1.0 / avg_time
            print(f"  Frame {i+1}/{num_frames}: FPS {fps:.1f} | Avg {avg_time*1000:.2f}ms")

    total_time = sum(frame_times)
    results.add_result(total_time, num_frames)
    results.print_summary()

    return results


def compare_benchmarks(*benchmarks: Tuple[str, BenchmarkResults]):
    """Compare multiple benchmarks side by side."""
    print(f"\n{'='*70}")
    print("Performance Comparison")
    print(f"{'='*70}")

    print(f"\n{'Benchmark':<35} {'Time (ms)':<15} {'Throughput':<15}")
    print("-" * 70)

    for name, results in benchmarks:
        stats = results.get_stats()
        print(f"{name:<35} {stats['avg_time']*1000:<15.2f} {stats['avg_throughput']:<15.1f}")

    # Calculate speedups
    if len(benchmarks) > 1:
        baseline_time = benchmarks[0][1].get_stats()['avg_time']

        print(f"\nSpeedup vs {benchmarks[0][0]}:")
        for name, results in benchmarks[1:]:
            stats = results.get_stats()
            speedup = baseline_time / stats['avg_time']
            print(f"  {name:<32} {speedup:.2f}x")


async def main():
    """Run all benchmarks."""
    print("=" * 70)
    print("AsyncDetector Performance Benchmarks")
    print("=" * 70)

    # Setup
    print("\nInitializing detector...")
    base_detector = YOLOv8Detector()
    base_detector.load_model('yolov8n.pt', device='cpu')

    async_detector = AsyncDetector(base_detector, max_workers=4, default_batch_size=8)

    # Test configuration
    num_images = 20
    images = create_test_images(num_images)

    print(f"Test configuration:")
    print(f"  Images: {num_images}")
    print(f"  Image size: 480x640x3")
    print(f"  Workers: {async_detector.max_workers}")

    # Run benchmarks
    print("\n" + "=" * 70)
    print("Running Benchmarks")
    print("=" * 70)

    # Benchmark 1: Sync detection
    sync_results = benchmark_sync_detection(async_detector, images, iterations=5)

    # Benchmark 2: Async detection
    async_results = await benchmark_async_detection(async_detector, images, iterations=5)

    # Benchmark 3: Batch detection
    batch_results = benchmark_batch_detection(async_detector, images, batch_sizes=[4, 8, 16], iterations=3)

    # Benchmark 4: Concurrent load
    concurrent_results = await benchmark_concurrent_load(async_detector, num_images=20, num_workers_list=[1, 2, 4, 8])

    # Benchmark 5: Video streaming
    video_results = await benchmark_video_streaming(async_detector, num_frames=100)

    # Compare main benchmarks
    compare_benchmarks(
        ("Sync Detection", sync_results),
        ("Async Detection (4 workers)", async_results),
        ("Batch Detection (size=8)", batch_results[8])
    )

    # Summary
    print(f"\n{'='*70}")
    print("Benchmark Summary")
    print(f"{'='*70}")

    async_stats = async_results.get_stats()
    video_stats = video_results.get_stats()

    print(f"\nKey Findings:")
    print(f"  1. Async speedup over sync: {sync_results.get_stats()['avg_time']/async_stats['avg_time']:.2f}x")
    print(f"  2. Average async FPS: {async_stats['avg_throughput']:.1f}")
    print(f"  3. Video streaming FPS: {video_stats['avg_throughput']:.1f}")
    print(f"  4. Target 30 FPS achieved: {'YES' if video_stats['avg_throughput'] >= 30 else 'NO'}")

    # Best configuration
    print(f"\nOptimal Configuration:")
    best_batch_size = max(batch_results.items(), key=lambda x: x[1].get_stats()['avg_throughput'])
    best_workers = max(concurrent_results.items(), key=lambda x: x[1].get_stats()['avg_throughput'])

    print(f"  Best batch size: {best_batch_size[0]} ({best_batch_size[1].get_stats()['avg_throughput']:.1f} FPS)")
    print(f"  Best workers: {best_workers[0]} ({best_workers[1].get_stats()['avg_throughput']:.1f} FPS)")

    # Cleanup
    async_detector.shutdown()

    print("\n" + "=" * 70)
    print("Benchmarks completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
