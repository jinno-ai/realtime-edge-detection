#!/usr/bin/env python3
"""
Run Object Detection

Usage:
    python scripts/run_detection.py --source video.mp4 --model yolov8n.pt
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.yolo_detector import YOLODetector


def main():
    parser = argparse.ArgumentParser(description=\"Run object detection\")
    parser.add_argument(\"--source\", required=True, help=\"Video source\")
    parser.add_argument(\"--model\", default=\"yolov8n.pt\", help=\"Model path\")
    parser.add_argument(\"--output\", help=\"Output video path\")
    parser.add_argument(\"--conf\", type=float, default=0.5, help=\"Confidence threshold\")
    
    args = parser.parse_args()
    
    # Create detector
    detector = YOLODetector(args.model, conf_threshold=args.conf)
    detector.load_model()
    
    # Run detection
    detector.detect_video(args.source, args.output)


if __name__ == \"__main__\":
    main()
