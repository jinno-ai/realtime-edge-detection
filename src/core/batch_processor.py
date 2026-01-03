"""
Batch processing module for efficient multi-image detection.

Provides memory-aware batch processing with automatic batch size optimization,
progress tracking, and error handling for large-scale image processing.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import csv

import numpy as np
import cv2


class BatchStatistics:
    """Tracks batch processing statistics."""

    def __init__(self):
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.total_images: int = 0
        self.successful: int = 0
        self.failed: int = 0
        self.processing_times: List[float] = []
        self.batch_sizes: List[int] = []
        self.peak_memory_mb: float = 0.0

    def record_batch(self, batch_size: int, processing_time: float, success_count: int):
        """Record statistics for a single batch."""
        self.total_images += batch_size
        self.successful += success_count
        self.failed += (batch_size - success_count)
        self.processing_times.append(processing_time)
        self.batch_sizes.append(batch_size)

    def finish(self):
        """Mark processing as complete."""
        self.end_time = time.time()

    @property
    def total_time(self) -> float:
        """Total processing time in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    @property
    def average_fps(self) -> float:
        """Average frames per second."""
        total_time = self.total_time
        return self.successful / total_time if total_time > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_time_seconds': round(self.total_time, 2),
            'total_images': self.total_images,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': f"{(self.successful / self.total_images * 100):.1f}%" if self.total_images > 0 else "0%",
            'average_fps': round(self.average_fps, 1),
            'batch_count': len(self.batch_sizes),
            'average_batch_size': round(np.mean(self.batch_sizes), 1) if self.batch_sizes else 0,
            'peak_memory_mb': round(self.peak_memory_mb, 1)
        }


class MemoryMonitor:
    """Monitors available memory (RAM and VRAM)."""

    @staticmethod
    def get_available_memory_mb() -> Tuple[float, Optional[float]]:
        """
        Get available memory in MB.

        Returns:
            Tuple of (cpu_memory_mb, gpu_memory_mb)
            gpu_memory_mb is None if CUDA is not available
        """
        # CPU memory
        try:
            import psutil
            cpu_memory = psutil.virtual_memory().available / (1024 * 1024)
        except ImportError:
            # Fallback if psutil not available
            cpu_memory = 2048.0  # Conservative estimate

        # GPU memory
        gpu_memory = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                gpu_used = torch.cuda.memory_allocated() / (1024 * 1024)
                gpu_memory = gpu_memory - gpu_used
        except Exception:
            pass

        return cpu_memory, gpu_memory

    @staticmethod
    def calculate_optimal_batch_size(
        image_size: Tuple[int, int],
        available_memory_mb: float,
        model_memory_mb: float = 500.0
    ) -> int:
        """
        Calculate optimal batch size based on available memory.

        Args:
            image_size: Image dimensions (height, width, channels)
            available_memory_mb: Available memory in MB
            model_memory_mb: Memory required for model in MB

        Returns:
            Optimal batch size (clamped to reasonable range)
        """
        h, w, c = image_size

        # Memory per image (uncompressed)
        image_memory_mb = (h * w * c * 4) / (1024 * 1024)  # 4 bytes per float32

        # Total memory per image in batch
        memory_per_image = model_memory_mb + image_memory_mb

        # Reserve 20% for safety
        usable_memory = available_memory_mb * 0.8

        # Calculate batch size
        batch_size = int(usable_memory / memory_per_image)

        # Clamp to reasonable range
        return max(1, min(batch_size, 128))


class BatchProcessor:
    """
    Orchestrates batch processing of images with memory management.

    Features:
    - Automatic batch size detection
    - Memory-aware processing
    - Progress tracking
    - Error handling and recovery
    - Statistics collection
    """

    def __init__(self, detector, batch_size: int = 32, auto_batch: bool = False):
        """
        Initialize batch processor.

        Args:
            detector: Detector instance implementing AbstractDetector interface
            batch_size: Batch size for processing (ignored if auto_batch=True)
            auto_batch: Whether to automatically determine batch size
        """
        self.detector = detector
        self.config = detector.config
        self.auto_batch = auto_batch
        self.batch_size = batch_size
        self.stats = BatchStatistics()
        self.error_log: List[Dict[str, Any]] = []

    def _load_images(self, image_dir: str) -> List[Tuple[str, np.ndarray]]:
        """
        Load all images from directory.

        Args:
            image_dir: Path to directory containing images

        Returns:
            List of (image_path, image_array) tuples
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_paths = []

        # Find all image files
        for ext in image_extensions:
            image_paths.extend(Path(image_dir).glob(f'*{ext}'))
            image_paths.extend(Path(image_dir).glob(f'*{ext.upper()}'))

        # Load images
        images = []
        for img_path in sorted(image_paths):
            try:
                img = cv2.imread(str(img_path))
                if img is not None:
                    images.append((str(img_path), img))
                else:
                    self.error_log.append({
                        'image': str(img_path),
                        'error': 'Failed to load image',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                self.error_log.append({
                    'image': str(img_path),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        return images

    def _determine_batch_size(self, images: List[Tuple[str, np.ndarray]]) -> int:
        """
        Determine batch size (automatic or fixed).

        Args:
            images: List of loaded images

        Returns:
            Batch size to use
        """
        if not self.auto_batch:
            return self.batch_size

        # Use first image to calculate batch size
        sample_image = images[0][1]
        h, w, c = sample_image.shape

        # Get available memory
        cpu_mem, gpu_mem = MemoryMonitor.get_available_memory_mb()

        # Use GPU memory if available, otherwise CPU
        available_mem = gpu_mem if gpu_mem else cpu_mem

        # Calculate optimal batch size
        batch_size = MemoryMonitor.calculate_optimal_batch_size(
            (h, w, c),
            available_mem,
            model_memory_mb=500.0  # Estimated model memory
        )

        print(f"   Auto-detected batch size: {batch_size} (based on {available_mem:.0f}MB available memory)")

        return batch_size

    def _save_csv_results(self, results: List[Dict[str, Any]], output_path: str):
        """
        Save detection results to CSV file.

        Args:
            results: List of detection results with metadata
            output_path: Path to output CSV file
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'class', 'confidence', 'x1', 'y1', 'x2', 'y2', 'time_ms']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for result in results:
                filename = result['filename']
                detections = result['detections']
                time_ms = result['time_ms']

                if not detections:
                    # Write empty row for images with no detections
                    writer.writerow({
                        'filename': filename,
                        'class': '',
                        'confidence': '',
                        'x1': '',
                        'y1': '',
                        'x2': '',
                        'y2': '',
                        'time_ms': f"{time_ms:.2f}"
                    })
                else:
                    for det in detections:
                        writer.writerow({
                            'filename': filename,
                            'class': det['class_name'],
                            'confidence': f"{det['confidence']:.3f}",
                            'x1': det['bbox'][0],
                            'y1': det['bbox'][1],
                            'x2': det['bbox'][2],
                            'y2': det['bbox'][3],
                            'time_ms': f"{time_ms:.2f}"
                        })

        print(f"\n💾 CSV results saved to: {output_path}")

    def process_directory(
        self,
        input_dir: str,
        output_csv: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> BatchStatistics:
        """
        Process all images in a directory.

        Args:
            input_dir: Path to input directory
            output_csv: Optional path to CSV output file
            output_dir: Optional path to save annotated images

        Returns:
            BatchStatistics object with processing results
        """
        print(f"\n📁 Loading images from: {input_dir}")
        images = self._load_images(input_dir)

        if not images:
            print("❌ No images found in directory")
            return self.stats

        print(f"✅ Loaded {len(images)} images")

        # Determine batch size
        self.batch_size = self._determine_batch_size(images)

        # Calculate number of batches
        num_batches = (len(images) + self.batch_size - 1) // self.batch_size
        print(f"\n🚀 Processing {len(images)} images in {num_batches} batches (batch size: {self.batch_size})")

        # Process batches
        all_results = []
        for batch_idx in range(0, len(images), self.batch_size):
            batch_end = min(batch_idx + self.batch_size, len(images))
            batch_images = images[batch_idx:batch_end]

            batch_num = batch_idx // self.batch_size + 1

            print(f"\n   Batch {batch_num}/{num_batches} (images {batch_idx + 1}-{batch_end})")

            # Process batch
            batch_results = self._process_batch(batch_images)
            all_results.extend(batch_results)

            # Update progress
            success_count = sum(1 for r in batch_results if r.get('success', True))
            self.stats.record_batch(len(batch_images), 0, success_count)

            # Show progress
            elapsed = self.stats.total_time
            eta = (elapsed / batch_num) * (num_batches - batch_num) if batch_num > 0 else 0
            fps = self.stats.average_fps

            print(f"   Progress: [{batch_num}/{num_batches}] | FPS: {fps:.1f} | ETA: {eta:.0f}s | Errors: {len(self.error_log)}")

        # Finish
        self.stats.finish()

        # Save results
        if output_csv:
            self._save_csv_results(all_results, output_csv)

        return self.stats

    def _process_batch(self, batch_images: List[Tuple[str, np.ndarray]]) -> List[Dict[str, Any]]:
        """
        Process a single batch of images.

        Args:
            batch_images: List of (image_path, image_array) tuples

        Returns:
            List of detection results
        """
        batch_start = time.time()
        results = []

        # Extract image arrays
        image_arrays = [img[1] for img in batch_images]
        image_paths = [img[0] for img in batch_images]

        try:
            # Run batch detection
            detections_list = self.detector.detect_batch(image_arrays)

            processing_time = (time.time() - batch_start) * 1000  # ms

            # Package results
            for img_path, detections in zip(image_paths, detections_list):
                results.append({
                    'filename': img_path,
                    'detections': detections,
                    'success': True,
                    'time_ms': processing_time / len(batch_images)
                })

        except Exception as e:
            # Log error and try individual processing
            error_msg = f"Batch processing failed: {str(e)}"
            print(f"   ⚠️  {error_msg}")
            print(f"   🔄 Falling back to individual processing...")

            for img_path, img_array in batch_images:
                try:
                    start = time.time()
                    detections = self.detector.detect(img_array)
                    processing_time = (time.time() - start) * 1000

                    results.append({
                        'filename': img_path,
                        'detections': detections,
                        'success': True,
                        'time_ms': processing_time
                    })
                except Exception as e2:
                    self.error_log.append({
                        'image': img_path,
                        'error': str(e2),
                        'timestamp': datetime.now().isoformat()
                    })
                    results.append({
                        'filename': img_path,
                        'detections': [],
                        'success': False,
                        'time_ms': 0
                    })

        return results

    def print_summary(self):
        """Print processing summary."""
        stats_dict = self.stats.to_dict()

        print("\n" + "=" * 60)
        print("📊 Batch Processing Statistics")
        print("=" * 60)
        print(f"\n   Total Images:     {stats_dict['total_images']}")
        print(f"   Successful:       {stats_dict['successful']} ({stats_dict['success_rate']})")
        print(f"   Failed:           {stats_dict['failed']}")
        print(f"   Total Time:       {stats_dict['total_time_seconds']}s")
        print(f"   Average FPS:      {stats_dict['average_fps']}")
        print(f"   Batch Count:      {stats_dict['batch_count']}")
        print(f"   Avg Batch Size:   {stats_dict['average_batch_size']}")
        print("=" * 60)

        if self.error_log:
            print(f"\n⚠️  Errors logged: {len(self.error_log)}")
            print("   See individual error entries above for details")
