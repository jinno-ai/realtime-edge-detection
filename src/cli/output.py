"""
Output format handlers for detection results.

This module provides handlers for exporting detection results in various formats:
JSON, CSV, COCO, and visual (annotated images).
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import cv2
import numpy as np


class OutputHandler:
    """Handle detection result output in various formats."""

    # Color map for different classes (BGR format for OpenCV)
    CLASS_COLORS = {
        'person': (0, 255, 0),      # Green
        'car': (255, 0, 0),         # Blue
        'truck': (0, 0, 255),       # Red
        'bicycle': (255, 255, 0),   # Cyan
        'motorcycle': (255, 0, 255), # Magenta
        'bus': (0, 255, 255),       # Yellow
        'default': (128, 128, 128)   # Gray
    }

    @staticmethod
    def get_color(class_name: str) -> tuple:
        """
        Get color for a given class name.

        Args:
            class_name: Name of the class

        Returns:
            BGR color tuple
        """
        return OutputHandler.CLASS_COLORS.get(class_name.lower(),
                                             OutputHandler.CLASS_COLORS['default'])

    @staticmethod
    def to_json(detections: List[Dict], metadata: Dict, output_path: Path) -> None:
        """
        Export detections to JSON format.

        Args:
            detections: List of detection dictionaries
            metadata: Metadata including model info, device, etc.
            output_path: Path to output JSON file
        """
        output = {
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'detections': detections,
            'total_detections': len(detections)
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    @staticmethod
    def to_csv(detections: List[Dict], output_path: Path) -> None:
        """
        Export detections to CSV format.

        Args:
            detections: List of detection dictionaries
            output_path: Path to output CSV file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['class', 'confidence', 'x1', 'y1', 'x2', 'y2'])

            # Data rows
            for det in detections:
                bbox = det['bbox']
                writer.writerow([
                    det['class_name'],
                    f"{det['confidence']:.4f}",
                    f"{bbox[0]:.2f}", f"{bbox[1]:.2f}",
                    f"{bbox[2]:.2f}", f"{bbox[3]:.2f}"
                ])

    @staticmethod
    def to_coco(detections: List[Dict], image_info: Dict, output_path: Path) -> None:
        """
        Export detections to COCO format.

        Args:
            detections: List of detection dictionaries
            image_info: Dictionary with image metadata (id, filename, width, height)
            output_path: Path to output COCO JSON file
        """
        # Build COCO-style JSON
        output = {
            'images': [{
                'id': image_info.get('id', 1),
                'file_name': image_info.get('filename', 'image.jpg'),
                'width': image_info.get('width', 0),
                'height': image_info.get('height', 0)
            }],
            'annotations': [],
            'categories': []
        }

        # Collect unique categories
        categories = {}
        for det in detections:
            class_id = det.get('class_id', 0)
            class_name = det['class_name']
            if class_id not in categories:
                categories[class_id] = {
                    'id': class_id,
                    'name': class_name,
                    'supercategory': 'object'
                }

        output['categories'] = list(categories.values())

        # Create annotations
        for ann_id, det in enumerate(detections, start=1):
            bbox = det['bbox']
            # Convert [x1, y1, x2, y2] to COCO [x, y, width, height]
            x, y = bbox[0], bbox[1]
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]

            output['annotations'].append({
                'id': ann_id,
                'image_id': image_info.get('id', 1),
                'category_id': det.get('class_id', 0),
                'bbox': [x, y, width, height],
                'area': width * height,
                'score': float(det['confidence'])
            })

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

    @staticmethod
    def draw_detections(image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on image.

        Args:
            image: Input image (numpy array)
            detections: List of detection dictionaries

        Returns:
            Image with drawn detections
        """
        image_copy = image.copy()

        for det in detections:
            bbox = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']

            # Get coordinates
            x1, y1, x2, y2 = map(int, bbox)

            # Get color for this class
            color = OutputHandler.get_color(class_name)

            # Draw bounding box
            cv2.rectangle(image_copy, (x1, y1), (x2, y2), color, 2)

            # Create label text
            label = f"{class_name}: {confidence:.2f}"

            # Get label size for background
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )

            # Draw label background
            cv2.rectangle(
                image_copy,
                (x1, y1 - label_height - baseline - 5),
                (x1 + label_width, y1),
                color,
                -1
            )

            # Draw label text
            cv2.putText(
                image_copy,
                label,
                (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

        return image_copy

    @staticmethod
    def to_visual(image: np.ndarray, detections: List[Dict], output_path: Path) -> None:
        """
        Save annotated image with detections.

        Args:
            image: Input image (numpy array)
            detections: List of detection dictionaries
            output_path: Path to output image file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Draw detections
        annotated_image = OutputHandler.draw_detections(image, detections)

        # Save image
        cv2.imwrite(str(output_path), annotated_image)
