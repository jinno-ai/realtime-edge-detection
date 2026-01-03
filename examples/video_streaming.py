"""
Video Streaming Example

Demonstrates real-time object detection on video streams using AsyncDetector.
This example shows how to achieve high FPS for video processing scenarios.
"""

import asyncio
import time
from pathlib import Path

import cv2
import numpy as np

from src.api import AsyncDetector
from src.detection.yolov8 import YOLOv8Detector


async def process_video_stream(
    detector: AsyncDetector,
    video_path: str,
    max_frames: int = None,
    display: bool = False
):
    """
    Process video stream with async detection.

    Args:
        detector: AsyncDetector instance
        video_path: Path to video file
        max_frames: Maximum number of frames to process (None = all)
        display: Whether to display video with detections
    """

    print(f"\nOpening video: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")

    if max_frames:
        print(f"  Processing max {max_frames} frames")

    # Processing variables
    frame_count = 0
    total_detections = 0
    processing_times = []

    print("\nStarting video processing...")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            if max_frames and frame_count >= max_frames:
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Async detection
            start = time.time()
            result = await detector.detect_async(frame_rgb)
            elapsed = time.time() - start

            processing_times.append(elapsed)
            frame_count += 1
            total_detections += result.metadata['num_detections']

            # Display progress every 30 frames
            if frame_count % 30 == 0:
                avg_time = np.mean(processing_times[-30:])
                current_fps = 1.0 / avg_time if avg_time > 0 else 0

                print(f"  Frame {frame_count}: {result.metadata['num_detections']} detections | "
                      f"Current FPS: {current_fps:.1f} | Avg: {avg_time*1000:.2f}ms")

            # Optional: Display frame with detections
            if display:
                # Draw detections
                frame_with_boxes = frame.copy()

                for box in result.boxes:
                    x1, y1, x2, y2 = box.astype(int)
                    cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Add info overlay
                info_text = f"Frame: {frame_count} | Detections: {result.metadata['num_detections']} | FPS: {1.0/elapsed:.1f}"
                cv2.putText(frame_with_boxes, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow('Video Stream', frame_with_boxes)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    finally:
        cap.release()
        if display:
            cv2.destroyAllWindows()

    # Calculate statistics
    total_time = sum(processing_times)
    avg_time = np.mean(processing_times)
    min_time = np.min(processing_times)
    max_time = np.max(processing_times)
    avg_fps = 1.0 / avg_time if avg_time > 0 else 0

    print(f"\n{'=' * 70}")
    print("Video Processing Statistics")
    print(f"{'=' * 70}")
    print(f"Frames processed:     {frame_count}")
    print(f"Total detections:     {total_detections}")
    print(f"Avg per frame:        {total_detections/frame_count:.1f}" if frame_count > 0 else "Avg per frame:        N/A")
    print(f"\nTiming Statistics:")
    print(f"  Total time:         {total_time:.2f}s")
    print(f"  Average:            {avg_time*1000:.2f}ms")
    print(f"  Min:                {min_time*1000:.2f}ms")
    print(f"  Max:                {max_time*1000:.2f}ms")
    print(f"\nPerformance:")
    print(f"  Average FPS:        {avg_fps:.1f}")
    print(f"  Target FPS:         30+")
    print(f"  Target achieved:    {'YES' if avg_fps >= 30 else 'NO'}")


async def simulate_video_stream(detector: AsyncDetector, num_frames: int = 100):
    """
    Simulate video stream processing with generated frames.

    Useful for testing without actual video files.
    """

    print(f"\nSimulating video stream with {num_frames} frames...")

    frame_count = 0
    processing_times = []
    total_detections = 0

    for i in range(num_frames):
        # Generate frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Async detection
        start = time.time()
        result = await detector.detect_async(frame)
        elapsed = time.time() - start

        processing_times.append(elapsed)
        frame_count += 1
        total_detections += result.metadata['num_detections']

        # Progress update
        if frame_count % 20 == 0:
            avg_time = np.mean(processing_times[-20:])
            current_fps = 1.0 / avg_time

            print(f"  Frame {frame_count}/{num_frames}: "
                  f"FPS: {current_fps:.1f} | Avg: {avg_time*1000:.2f}ms")

    # Statistics
    avg_time = np.mean(processing_times)
    avg_fps = 1.0 / avg_time

    print(f"\nSimulation Results:")
    print(f"  Frames processed:    {frame_count}")
    print(f"  Total detections:    {total_detections}")
    print(f"  Average FPS:         {avg_fps:.1f}")
    print(f"  Average latency:     {avg_time*1000:.2f}ms")
    print(f"  Target achieved:     {'YES' if avg_fps >= 30 else 'NO'}")


async def main():
    """Main video streaming example."""

    print("=" * 70)
    print("Video Streaming Example")
    print("=" * 70)

    # Initialize detector
    print("\n1. Initializing detector...")
    base_detector = YOLOv8Detector()
    base_detector.load_model('yolov8n.pt', device='cpu')

    # Create async detector with 4 workers for parallel processing
    async_detector = AsyncDetector(
        base_detector,
        max_workers=4,
        default_batch_size=8
    )

    print(f"   Max workers: {async_detector.max_workers}")
    print(f"   Detector ready!")

    # Example 1: Simulated video stream
    print("\n" + "=" * 70)
    print("Example 1: Simulated Video Stream")
    print("=" * 70)

    await simulate_video_stream(async_detector, num_frames=50)

    # Example 2: Real video file (if available)
    print("\n" + "=" * 70)
    print("Example 2: Real Video File Processing")
    print("=" * 70)

    video_path = "data/test_video.mp4"

    if Path(video_path).exists():
        await process_video_stream(
            async_detector,
            video_path,
            max_frames=100,  # Process first 100 frames
            display=False    # Set to True to show video window
        )
    else:
        print(f"\nVideo file not found: {video_path}")
        print("Skipping real video processing example.")
        print("To test with real video, place a video file at data/test_video.mp4")

    # Example 3: Real-time processing simulation
    print("\n" + "=" * 70)
    print("Example 3: Real-Time Processing Simulation")
    print("=" * 70)

    print("\nSimulating real-time video stream (30 FPS target)...")

    num_frames = 60
    frame_interval = 1.0 / 30  # 30 FPS

    start_time = time.time()
    frame_times = []

    for i in range(num_frames):
        frame_start = time.time()

        # Generate frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Detect
        result = await async_detector.detect_async(frame)

        frame_elapsed = time.time() - frame_start
        frame_times.append(frame_elapsed)

        # Simulate frame interval (real-time constraint)
        elapsed_total = time.time() - start_time
        expected_time = (i + 1) * frame_interval

        if elapsed_total < expected_time:
            await asyncio.sleep(expected_time - elapsed_total)

        if (i + 1) % 15 == 0:
            avg_processing = np.mean(frame_times[-15:])
            print(f"  Frame {i+1}/{num_frames}: Processing time {avg_processing*1000:.2f}ms")

    total_time = time.time() - start_time
    actual_fps = num_frames / total_time
    avg_processing_time = np.mean(frame_times)

    print(f"\nReal-Time Simulation Results:")
    print(f"  Total time:          {total_time:.2f}s")
    print(f"  Actual FPS:          {actual_fps:.1f}")
    print(f"  Target FPS:          30.0")
    print(f"  Avg processing time: {avg_processing_time*1000:.2f}ms")
    print(f"  Real-time capable:   {'YES' if avg_processing_time <= frame_interval else 'NO'}")

    # Cleanup
    print("\n" + "=" * 70)
    async_detector.shutdown()
    print("Detector shutdown complete")

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
