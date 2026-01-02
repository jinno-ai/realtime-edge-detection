"""
Basic Usage Example for Real-time Edge Detection

This example demonstrates how to:
1. Load YOLO model
2. Detect objects in images
3. Process video streams
4. Draw detection results
"""

import cv2
import numpy as np
from src.models.yolo_detector import YOLODetector


def example_image_detection():
    """Example of detecting objects in an image"""
    print("=" * 60)
    print("YOLO Detector - Image Detection")
    print("=" * 60)

    # Initialize detector
    print("\n🔧 Initializing detector...")
    detector = YOLODetector(
        model_path="yolov8n.pt",  # Nano model for speed
        conf_threshold=0.5,
        iou_threshold=0.4
    )

    # Load model
    print("🧠 Loading model...")
    detector.load_model()

    # Create a test image (in real use, load from file)
    print("\n📸 Creating test image...")
    test_image = np.zeros((640, 640, 3), dtype=np.uint8)
    test_image[:] = (100, 150, 200)  # Blue background

    # Add some random shapes
    cv2.rectangle(test_image, (100, 100), (300, 300), (255, 255, 255), -1)
    cv2.circle(test_image, (450, 200), 80, (255, 0, 0), -1)

    print("\n🔍 Detecting objects...")
    detections = detector.detect(test_image)

    print(f"\nFound {len(detections)} objects:")
    for i, det in enumerate(detections, 1):
        bbox = det['bbox']
        print(f"\n{i}. {det['class_name']}")
        print(f"   Confidence: {det['confidence']:.3f}")
        print(f"   Bounding Box: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")

    # Draw detections
    result_image = detector.draw_detections(test_image, detections)

    # Save result
    output_path = "detection_result.jpg"
    cv2.imwrite(output_path, result_image)
    print(f"\n💾 Saved result to: {output_path}")


def example_webcam_detection():
    """Example of real-time webcam detection"""
    print("\n" + "=" * 60)
    print("Real-time Webcam Detection")
    print("=" * 60)

    # Initialize detector
    print("\n🔧 Initializing detector...")
    detector = YOLODetector(
        model_path="yolov8n.pt",
        conf_threshold=0.5,
        iou_threshold=0.4
    )

    print("🧠 Loading model...")
    detector.load_model()

    # Open webcam
    print("\n📹 Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Could not open webcam")
        return

    print("✅ Webcam opened successfully!")
    print("\nPress 'q' to quit")

    frame_count = 0
    total_fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect objects
            import time
            start_time = time.time()
            detections = detector.detect(frame)
            inference_time = time.time() - start_time
            fps = 1 / inference_time if inference_time > 0 else 0

            # Draw detections
            frame = detector.draw_detections(frame, detections)

            # Add FPS counter
            cv2.putText(
                frame,
                f"FPS: {fps:.1f} | Objects: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            # Display
            cv2.imshow("YOLO Detection", frame)

            # Update stats
            frame_count += 1
            total_fps += fps

            # Quit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        if frame_count > 0:
            avg_fps = total_fps / frame_count
            print(f"\n📊 Statistics:")
            print(f"   Frames processed: {frame_count}")
            print(f"   Average FPS: {avg_fps:.1f}")


def example_video_detection():
    """Example of processing video file"""
    print("\n" + "=" * 60)
    print("Video File Processing")
    print("=" * 60)

    # Initialize detector
    print("\n🔧 Initializing detector...")
    detector = YOLODetector(
        model_path="yolov8n.pt",
        conf_threshold=0.5,
        iou_threshold=0.4
    )

    print("🧠 Loading model...")
    detector.load_model()

    # In real use, provide actual video path
    video_path = "input_video.mp4"
    output_path = "output_video.mp4"

    print(f"\n📹 Processing video: {video_path}")
    print(f"💾 Output will be saved to: {output_path}")

    # Note: This requires an actual video file
    print("\n⚠️  This example requires an actual video file")
    print("   To use it:")
    print("   1. Place your video at 'input_video.mp4'")
    print("   2. Uncomment the line below")
    print("   3. Run this script")

    # Uncomment to process actual video:
    # detector.detect_video(video_path, output_path)


def example_batch_detection():
    """Example of batch image processing"""
    print("\n" + "=" * 60)
    print("Batch Image Processing")
    print("=" * 60)

    # Initialize detector
    print("\n🔧 Initializing detector...")
    detector = YOLODetector(
        model_path="yolov8n.pt",
        conf_threshold=0.5,
        iou_threshold=0.4
    )

    print("🧠 Loading model...")
    detector.load_model()

    # Create test images
    print("\n📸 Creating test images...")
    test_images = []

    for i in range(5):
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        test_images.append(img)

    print(f"Processing {len(test_images)} images...")

    total_detections = 0
    for i, image in enumerate(test_images, 1):
        detections = detector.detect(image)
        total_detections += len(detections)
        print(f"  Image {i}: {len(detections)} objects detected")

    print(f"\n✅ Total detections: {total_detections}")


def example_custom_classes():
    """Example of filtering by specific classes"""
    print("\n" + "=" * 60)
    print("Filter by Specific Classes")
    print("=" * 60)

    detector = YOLODetector("yolov8n.pt")
    detector.load_model()

    print("\n🎯 Filtering for 'person' class only...")
    print("(This is useful for people counting applications)")

    # In real use, you would filter detections:
    # detections = detector.detect(image)
    # person_detections = [d for d in detections if d['class_name'] == 'person']
    # print(f"Found {len(person_detections)} people")

    print("\n✅ Check the model's available classes:")
    if hasattr(detector.model, 'names'):
        for class_id, class_name in detector.model.names.items():
            print(f"  {class_id}: {class_name}")


if __name__ == "__main__":
    import sys

    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1]
        else:
            mode = "image"

        if mode == "image":
            example_image_detection()
        elif mode == "webcam":
            example_webcam_detection()
        elif mode == "video":
            example_video_detection()
        elif mode == "batch":
            example_batch_detection()
        elif mode == "classes":
            example_custom_classes()
        else:
            print(f"Unknown mode: {mode}")
            print("\nAvailable modes:")
            print("  image   - Detect objects in test image")
            print("  webcam  - Real-time webcam detection")
            print("  video   - Process video file")
            print("  batch   - Batch process multiple images")
            print("  classes - Show available object classes")

        print("\n" + "=" * 60)
        print("Example Complete!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
