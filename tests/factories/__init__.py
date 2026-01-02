"""
Test data factories for generating test samples
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import random


class ImageFactory:
    """Factory for creating test images"""

    @staticmethod
    def create_bgr(
        width: int = 640,
        height: int = 480,
        color: Optional[Tuple[int, int, int]] = None
    ) -> np.ndarray:
        """
        Create BGR image (OpenCV format)

        Args:
            width: Image width
            height: Image height
            color: Solid color (B, G, R) or None for random

        Returns:
            BGR image array
        """
        if color:
            return np.full((height, width, 3), color, dtype=np.uint8)
        return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

    @staticmethod
    def create_rgb(
        width: int = 640,
        height: int = 480
    ) -> np.ndarray:
        """Create RGB image"""
        return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

    @staticmethod
    def create_grayscale(
        width: int = 640,
        height: int = 480
    ) -> np.ndarray:
        """Create grayscale image"""
        return np.random.randint(0, 255, (height, width), dtype=np.uint8)

    @staticmethod
    def create_with_object(
        width: int = 640,
        height: int = 480,
        bbox: Tuple[int, int, int, int] = (100, 100, 200, 200),
        color: Tuple[int, int, int] = (255, 0, 0)
    ) -> np.ndarray:
        """
        Create image with a colored object (for testing detection)

        Args:
            width: Image width
            height: Image height
            bbox: Bounding box (x1, y1, x2, y2)
            color: Object color (B, G, R)

        Returns:
            Image with colored rectangle
        """
        image = ImageFactory.create_bgr(width, height, color=(0, 0, 0))
        x1, y1, x2, y2 = bbox
        image[y1:y2, x1:x2] = color
        return image

    @staticmethod
    def create_batch(
        count: int = 5,
        width: int = 640,
        height: int = 480
    ) -> List[np.ndarray]:
        """Create batch of images"""
        return [ImageFactory.create_bgr(width, height) for _ in range(count)]


class BBoxFactory:
    """Factory for creating bounding boxes"""

    @staticmethod
    def create(
        x1: int = 100,
        y1: int = 100,
        x2: int = 200,
        y2: int = 200
    ) -> List[int]:
        """Create single bounding box"""
        return [x1, y1, x2, y2]

    @staticmethod
    def create_random(
        image_width: int = 640,
        image_height: int = 480,
        count: int = 3,
        min_size: int = 50,
        max_size: int = 150
    ) -> List[List[int]]:
        """
        Create random bounding boxes within image bounds

        Args:
            image_width: Maximum width
            image_height: Maximum height
            count: Number of boxes
            min_size: Minimum box size
            max_size: Maximum box size

        Returns:
            List of bounding boxes
        """
        bboxes = []
        for _ in range(count):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x1 = random.randint(0, max(0, image_width - w))
            y1 = random.randint(0, max(0, image_height - h))
            x2 = x1 + w
            y2 = y1 + h
            bboxes.append([x1, y1, x2, y2])
        return bboxes

    @staticmethod
    def create_overlapping(
        center_x: int = 320,
        center_y: int = 240,
        count: int = 3
    ) -> List[List[int]]:
        """Create overlapping bounding boxes (for IOU testing)"""
        bboxes = []
        for i in range(count):
            offset = i * 20
            size = 100 + offset
            x1 = center_x - size // 2
            y1 = center_y - size // 2
            x2 = center_x + size // 2
            y2 = center_y + size // 2
            bboxes.append([x1, y1, x2, y2])
        return bboxes


class DetectionFactory:
    """Factory for creating detection results"""

    @staticmethod
    def create(
        bbox: List[int],
        confidence: float = 0.85,
        class_id: int = 0,
        class_name: str = "person"
    ) -> Dict[str, Any]:
        """Create single detection"""
        return {
            'bbox': bbox,
            'confidence': confidence,
            'class_id': class_id,
            'class_name': class_name
        }

    @staticmethod
    def create_multiple(
        count: int = 3,
        classes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Create multiple detections"""
        if classes is None:
            classes = ['person', 'car', 'dog']

        detections = []
        for i in range(count):
            bbox = BBoxFactory.create_random()[0]
            class_name = classes[i % len(classes)]
            detections.append(DetectionFactory.create(
                bbox=bbox,
                confidence=random.uniform(0.5, 0.99),
                class_id=i % len(classes),
                class_name=class_name
            ))
        return detections

    @staticmethod
    def create_with_low_confidence() -> List[Dict[str, Any]]:
        """Create detections with low confidence (for threshold testing)"""
        return [
            DetectionFactory.create(
                bbox=BBoxFactory.create(),
                confidence=0.3,  # Below threshold
                class_name='person'
            ),
            DetectionFactory.create(
                bbox=BBoxFactory.create_random()[0],
                confidence=0.6,  # Above threshold
                class_name='car'
            )
        ]


class VideoFactory:
    """Factory for video-related test data"""

    @staticmethod
    def create_frames(
        count: int = 10,
        width: int = 640,
        height: int = 480
    ) -> List[np.ndarray]:
        """Create sequence of video frames"""
        return ImageFactory.create_batch(count, width, height)

    @staticmethod
    def create_params(
        fps: int = 30,
        frame_count: int = 300,
        width: int = 640,
        height: int = 480
    ) -> Dict[str, Any]:
        """Create video parameters"""
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': frame_count / fps
        }


class ConfigFactory:
    """Factory for creating test configurations"""

    @staticmethod
    def create_valid_config() -> Dict[str, Any]:
        """Create valid detection config"""
        return {
            'model': {
                'type': 'yolo_v8',
                'path': 'yolov8n.pt'
            },
            'detection': {
                'confidence_threshold': 0.5,
                'iou_threshold': 0.4,
                'max_detections': 100
            },
            'preprocessing': {
                'target_size': [640, 640],
                'normalize': True
            }
        }

    @staticmethod
    def create_config_with_invalid_threshold() -> Dict[str, Any]:
        """Create config with invalid threshold (> 1.0)"""
        config = ConfigFactory.create_valid_config()
        config['detection']['confidence_threshold'] = 1.5
        return config

    @staticmethod
    def create_config_with_negative_threshold() -> Dict[str, Any]:
        """Create config with negative threshold (< 0.0)"""
        config = ConfigFactory.create_valid_config()
        config['detection']['iou_threshold'] = -0.1
        return config
