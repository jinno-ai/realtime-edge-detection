"""
Interactive detection mode with real-time preview.

This module implements interactive detection with OpenCV display window,
keyboard controls, and real-time statistics overlay.
"""

import cv2
import time
from pathlib import Path
from typing import Dict, Any

from src.cli.metrics import MetricsTracker
from src.cli.output import OutputHandler


def run_interactive_detection(detector, input_path: Path,
                              config_mgr: Any, metrics: MetricsTracker) -> None:
    """
    Run detection in interactive mode with real-time preview.

    Args:
        detector: YOLO detector instance
        input_path: Path to input video or image
        config_mgr: Configuration manager
        metrics: Metrics tracker
    """
    # Check if input is video or image
    is_video = input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']

    if is_video:
        _run_interactive_video(detector, input_path, metrics)
    else:
        _run_interactive_image(detector, input_path, metrics)


def _run_interactive_video(detector, video_path: Path, metrics: MetricsTracker) -> None:
    """
    Run interactive detection on video.

    Args:
        detector: YOLO detector instance
        video_path: Path to input video
        metrics: Metrics tracker
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\nInteractive Mode:")
    print(f"  Video: {video_path.name}")
    print(f"  Resolution: {width}x{height} @ {fps:.2f} FPS")
    print(f"\nControls:")
    print(f"  Press 'q' to quit")
    print(f"  Press 's' to save current frame")
    print(f"  Press 'p' to pause/resume")
    print(f"  Press 'r' to reset metrics")
    print()

    paused = False
    frame_count = 0
    total_time = 0
    total_detections = 0
    frame_saved_count = 0

    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("\nEnd of video reached")
                    break

                # Detect
                metrics.start_inference()
                results = detector(frame)
                inference_time = metrics.end_inference()

                # Parse results
                detections = _parse_yolo_results(results, frame.shape)
                total_detections += len(detections)

                # Draw detections
                frame = OutputHandler.draw_detections(frame, detections)

                # Calculate stats
                fps_inst = 1.0 / inference_time if inference_time > 0 else 0
                total_time += inference_time
                avg_fps = (frame_count + 1) / total_time if total_time > 0 else 0

                # Draw stats overlay
                stats_text = (
                    f"Frame: {frame_count} | "
                    f"FPS: {fps_inst:.1f} (Avg: {avg_fps:.1f}) | "
                    f"Objects: {len(detections)} (Total: {total_detections})"
                )
                cv2.rectangle(frame, (0, 0), (width, 40), (0, 0, 0), -1)
                cv2.putText(frame, stats_text, (10, 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow("Interactive Detection", frame)

                frame_count += 1

            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                output_path = f"frame_{frame_count:06d}.jpg"
                cv2.imwrite(output_path, frame)
                frame_saved_count += 1
                print(f"Saved: {output_path}")
            elif key == ord('p'):
                paused = not paused
                print("Paused" if paused else "Resumed")
            elif key == ord('r'):
                metrics.reset()
                frame_count = 0
                total_time = 0
                total_detections = 0
                print("Metrics reset")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        # Print summary
        avg_fps = frame_count / total_time if total_time > 0 else 0
        print(f"\nInteractive Session Summary:")
        print(f"  Frames processed: {frame_count}")
        print(f"  Average FPS: {avg_fps:.1f}")
        print(f"  Total detections: {total_detections}")
        print(f"  Frames saved: {frame_saved_count}")


def _run_interactive_image(detector, image_path: Path, metrics: MetricsTracker) -> None:
    """
    Run interactive detection on single image.

    Args:
        detector: YOLO detector instance
        image_path: Path to input image
        metrics: Metrics tracker
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Could not load image: {image_path}")
        return

    print(f"\nInteractive Mode:")
    print(f"  Image: {image_path.name}")
    print(f"  Resolution: {image.shape[1]}x{image.shape[0]}")
    print(f"\nControls:")
    print(f"  Press 'q' to quit")
    print(f"  Press 's' to save result")
    print()

    # Detect
    metrics.start_inference()
    results = detector(image)
    inference_time = metrics.end_inference()

    # Parse results
    detections = _parse_yolo_results(results, image.shape)

    # Draw detections
    image = OutputHandler.draw_detections(image, detections)

    # Draw stats
    fps = 1.0 / inference_time if inference_time > 0 else 0
    stats_text = (
        f"Objects: {len(detections)} | "
        f"Time: {inference_time*1000:.1f}ms | "
        f"FPS: {fps:.1f}"
    )
    cv2.rectangle(image, (0, 0), (image.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(image, stats_text, (10, 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Interactive Detection", image)

    saved = False
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and not saved:
            output_path = f"{image_path.stem}_detected{image_path.suffix}"
            cv2.imwrite(output_path, image)
            print(f"Saved: {output_path}")
            saved = True

    cv2.destroyAllWindows()

    print(f"\nDetection Summary:")
    print(f"  Objects detected: {len(detections)}")
    print(f"  Inference time: {inference_time*1000:.1f}ms")
    print(f"  FPS: {fps:.1f}")


def _parse_yolo_results(results, image_shape) -> list:
    """
    Parse YOLO results into standard format.

    Args:
        results: YOLO results object
        image_shape: Shape of original image (h, w, c)

    Returns:
        List of detection dictionaries
    """
    detections = []

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            # Get confidence and class
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = result.names[class_id]

            detections.append({
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'confidence': confidence,
                'class_id': class_id,
                'class_name': class_name
            })

    return detections
