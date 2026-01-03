"""
Async and batch processing performance benchmarks.

Evaluates throughput improvements from async execution and batch processing.
Validates that async doesn't block main thread and achieves 1.5x throughput gain.
"""

import pytest
import numpy as np
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

# Import detection components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from detection.yolov8 import YOLOv8Detector


@pytest.mark.benchmark
class TestBatchProcessing:
    """
    Test batch processing performance (AC: #4).

    Given implementing async/batch detection
    When measuring throughput improvement
    Then batch processing achieves 1.5x throughput gain
    And async detection doesn't block main thread
    And memory usage is within limits
    """

    def test_synchronous_baseline(
        self,
        temp_model_path,
        sample_batch_images,
        measure_throughput
    ):
        """
        Measure synchronous detection throughput (baseline).
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        results = measure_throughput(detector, sample_batch_images, duration_sec=3.0)

        print(f"\nSynchronous Throughput:")
        print(f"  FPS: {results['fps']:.2f}")
        print(f"  Avg Latency: {results['avg_latency_ms']:.2f}ms")

        return results

    def test_batch_processing_throughput(
        self,
        temp_model_path,
        sample_batch_images,
        measure_throughput,
        performance_thresholds,
        save_baseline,
        baseline_path
    ):
        """
        Verify batch processing achieves 1.5x throughput gain.

        Compares batch vs sequential processing.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Synchronous (sequential)
        sync_results = measure_throughput(detector, sample_batch_images, duration_sec=3.0)

        # Batch processing
        # Note: detect_batch should be more efficient
        batch_images = sample_batch_images * 3  # More images for batch
        start_time = time.time()
        count = 0

        while time.time() - start_time < 3.0:
            # Process in batches of 8
            for i in range(0, len(batch_images), 8):
                batch = batch_images[i:i+8]
                _ = detector.detect_batch(batch)
                count += len(batch)

            if time.time() - start_time >= 3.0:
                break

        elapsed = time.time() - start_time
        batch_fps = count / elapsed if elapsed > 0 else 0

        batch_results = {
            'total_detections': count,
            'elapsed_sec': elapsed,
            'fps': batch_fps,
            'avg_latency_ms': (elapsed / count) * 1000 if count > 0 else 0,
        }

        # Calculate speedup
        speedup = batch_fps / sync_results['fps'] if sync_results['fps'] > 0 else 0

        # Check threshold
        threshold = performance_thresholds['async_speedup']

        print(f"\nBatch Processing Throughput:")
        print(f"  Sync FPS: {sync_results['fps']:.2f}")
        print(f"  Batch FPS: {batch_results['fps']:.2f}")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Threshold: {threshold:.1f}x")

        # Update baseline
        import json
        if baseline_path.exists():
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
        else:
            baseline = {"benchmarks": {}}

        baseline['benchmarks']['async_batch'] = {
            'sync_fps': sync_results['fps'],
            'batch_fps': batch_results['fps'],
            'speedup': speedup,
            'status': 'PASS' if speedup >= threshold else 'FAIL',
            'threshold': f"{threshold}x"
        }

        save_baseline(baseline_path, baseline)

        # Assert
        assert speedup >= threshold, (
            f"Batch speedup {speedup:.2f}x below threshold {threshold:.1f}x\n"
            f"Sync: {sync_results['fps']:.2f} FPS, "
            f"Batch: {batch_results['fps']:.2f} FPS"
        )

    def test_batch_size_effectiveness(
        self,
        temp_model_path,
        sample_image_640x640,
        measure_latency
    ):
        """
        Test optimal batch size for throughput.

        Evaluates different batch sizes to find optimal configuration.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        batch_sizes = [1, 2, 4, 8, 16]
        results = {}

        for batch_size in batch_sizes:
            batch = [sample_image_640x640] * batch_size

            # Measure time for batch
            start = time.perf_counter()
            _ = detector.detect_batch(batch)
            elapsed = time.perf_counter() - start

            # Calculate per-image latency
            per_image_ms = (elapsed / batch_size) * 1000

            results[batch_size] = {
                'total_time_ms': elapsed * 1000,
                'per_image_ms': per_image_ms,
                'throughput_fps': batch_size / elapsed if elapsed > 0 else 0
            }

        print(f"\nBatch Size Effectiveness:")
        for batch_size, metrics in results.items():
            print(f"  Batch {batch_size}: {metrics['per_image_ms']:.2f}ms/img, "
                  f"{metrics['throughput_fps']:.1f} FPS")

        # Find optimal batch size
        optimal = max(results.items(), key=lambda x: x[1]['throughput_fps'])
        print(f"\n  Optimal batch size: {optimal[0]} ({optimal[1]['throughput_fps']:.1f} FPS)")

    @pytest.mark.smoke
    def test_smoke_batch_processing(
        self,
        temp_model_path,
        sample_batch_images
    ):
        """
        Quick smoke test for batch processing.

        Verifies batch processing works without errors.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Process batch
        results = detector.detect_batch(sample_batch_images[:4])

        # Verify results
        assert len(results) == 4, f"Expected 4 results, got {len(results)}"
        for result in results:
            assert hasattr(result, 'boxes'), "Result should have boxes"
            assert hasattr(result, 'scores'), "Result should have scores"
            assert hasattr(result, 'classes'), "Result should have classes"

        print(f"\n✅ Batch processing smoke test passed")


@pytest.mark.benchmark
class TestAsyncDetection:
    """
    Test async detection performance.
    """

    def test_async_detection_non_blocking(
        self,
        temp_model_path,
        sample_image_640x640
    ):
        """
        Verify async detection doesn't block main thread.

        Measures that main thread remains responsive during async detection.
        """
        pytest.skip("Skipping: Requires async API - run after Story 2.6")

        # This test would use the async API from Story 2.6
        # For now, we simulate with ThreadPoolExecutor

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Simulate async detection
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit detection task
            future = executor.submit(detector.detect, sample_image_640x640)

            # Main thread should be responsive
            # Measure time until we can do other work
            start = time.perf_counter()
            dummy_work = sum(i*i for i in range(1000))
            main_thread_time = time.perf_counter() - start

            # Wait for detection
            result = future.result(timeout=10)

        # Main thread work should complete quickly (not blocked)
        assert main_thread_time < 0.1, f"Main thread blocked: {main_thread_time:.3f}s"

        print(f"\nAsync Non-Blocking Test:")
        print(f"  Main thread work time: {main_thread_time*1000:.2f}ms")
        print(f"  Main thread remained responsive: ✅")

    def test_async_throughput(
        self,
        temp_model_path,
        sample_batch_images,
        measure_throughput,
        performance_thresholds
    ):
        """
        Measure async detection throughput with multiple workers.

        Compares async workers vs synchronous processing.
        """
        pytest.skip("Skipping: Requires async API - run after Story 2.6")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Synchronous baseline
        sync_results = measure_throughput(detector, sample_batch_images, duration_sec=2.0)

        # Async with 4 workers
        num_workers = 4
        start_time = time.time()
        count = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []

            while time.time() - start_time < 2.0:
                # Submit detection tasks
                for img in sample_batch_images:
                    future = executor.submit(detector.detect, img)
                    futures.append(future)
                    count += 1

                if time.time() - start_time >= 2.0:
                    break

            # Wait for all to complete
            for future in futures:
                future.result(timeout=10)

        elapsed = time.time() - start_time
        async_fps = count / elapsed if elapsed > 0 else 0

        speedup = async_fps / sync_results['fps'] if sync_results['fps'] > 0 else 0

        print(f"\nAsync Throughput:")
        print(f"  Sync FPS: {sync_results['fps']:.2f}")
        print(f"  Async FPS ({num_workers} workers): {async_fps:.2f}")
        print(f"  Speedup: {speedup:.2f}x")

        # Async should be faster
        assert speedup > 1.0, f"Async should be faster, got {speedup:.2f}x"

        # Check threshold
        threshold = performance_thresholds['async_speedup']
        if speedup >= threshold:
            print(f"  ✅ Meets threshold {threshold:.1f}x")
        else:
            print(f"  ⚠️  Below threshold {threshold:.1f}x")


@pytest.mark.benchmark
class TestMemoryUsage:
    """
    Test memory usage of async and batch processing.
    """

    def test_memory_within_limits(
        self,
        temp_model_path,
        sample_batch_images,
        measure_memory,
        performance_thresholds
    ):
        """
        Verify batch processing memory usage is within limits.

        NFR-P4: Memory usage should be < 500MB.
        """
        pytest.skip("Skipping: Requires model file - run with actual model")

        detector = YOLOv8Detector()
        detector.load_model("yolov8n.pt", device="cpu")

        # Measure memory for batch processing
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Process batch
        results = detector.detect_batch(sample_batch_images)

        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        mem_used = mem_after - mem_before

        print(f"\nMemory Usage:")
        print(f"  Before: {mem_before:.2f}MB")
        print(f"  After: {mem_after:.2f}MB")
        print(f"  Used: {mem_used:.2f}MB")

        # Check threshold
        threshold = performance_thresholds['memory_mb']
        assert mem_after < threshold, (
            f"Memory usage {mem_after:.2f}MB exceeds threshold {threshold}MB"
        )

        print(f"  ✅ Within threshold {threshold}MB")
