"""
Real-time Edge Detection

Low-latency object detection optimized for edge devices.
"""

from src.models.yolo_detector import YOLODetector
from src.preprocessing.image_processor import ImageProcessor, ImageAugmentor, EdgeOptimizer
from src.utils.video_utils import VideoCapture, VideoWriter, FrameProcessor, stream_frames
from src.api.async_detector import AsyncDetector

__version__ = "0.1.0"
__author__ = "Jinno"

__all__ = [
    'YOLODetector',
    'ImageProcessor',
    'ImageAugmentor',
    'EdgeOptimizer',
    'VideoCapture',
    'VideoWriter',
    'FrameProcessor',
    'stream_frames',
    'AsyncDetector'
]
