"""
Image Preprocessing for Edge Detection

Handles image preprocessing, augmentation, and optimization for edge devices.
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict, Any


class ImageProcessor:
    """Image preprocessing for object detection"""
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True,
        mean: Tuple[float, ...] = (0.485, 0.456, 0.406),
        std: Tuple[float, ...] = (0.229, 0.224, 0.225)
    ):
        self.target_size = target_size
        self.normalize = normalize
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            Preprocessed image
        """
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize
        image = self.resize(image, self.target_size)
        
        # Convert to float32
        image = image.astype(np.float32) / 255.0
        
        # Normalize
        if self.normalize:
            image = (image - self.mean) / self.std
        
        # Add batch dimension and transpose to NCHW
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)
        
        return image
    
    def resize(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int],
        keep_ratio: bool = True
    ) -> np.ndarray:
        """
        Resize image while optionally keeping aspect ratio.
        
        Args:
            image: Input image
            target_size: Target (width, height)
            keep_ratio: Whether to keep aspect ratio
            
        Returns:
            Resized image
        """
        if not keep_ratio:
            return cv2.resize(image, target_size)
        
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # Calculate scale
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(image, (new_w, new_h))
        
        # Pad to target size
        padded = np.zeros((target_h, target_w, 3), dtype=image.dtype)
        pad_x = (target_w - new_w) // 2
        pad_y = (target_h - new_h) // 2
        padded[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
        
        return padded
    
    def letterbox(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """
        Letterbox resize (YOLO style).
        
        Args:
            image: Input image
            target_size: Target size
            color: Padding color
            
        Returns:
            Tuple of (resized image, scale, padding)
        """
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # Calculate scale
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Calculate padding
        pad_w = (target_w - new_w) // 2
        pad_h = (target_h - new_h) // 2
        
        # Create padded image
        padded = np.full((target_h, target_w, 3), color, dtype=np.uint8)
        padded[pad_h:pad_h + new_h, pad_w:pad_w + new_w] = resized
        
        return padded, scale, (pad_w, pad_h)
    
    def batch_preprocess(self, images: List[np.ndarray]) -> np.ndarray:
        """Preprocess a batch of images"""
        processed = [self.preprocess(img) for img in images]
        return np.concatenate(processed, axis=0)


class ImageAugmentor:
    """Image augmentation for training"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)
    
    def augment(
        self,
        image: np.ndarray,
        bboxes: Optional[List[List[float]]] = None
    ) -> Tuple[np.ndarray, Optional[List[List[float]]]]:
        """
        Apply random augmentations.
        
        Args:
            image: Input image
            bboxes: Optional bounding boxes [x1, y1, x2, y2]
            
        Returns:
            Augmented image and bboxes
        """
        # Random horizontal flip
        if np.random.random() > 0.5:
            image, bboxes = self.horizontal_flip(image, bboxes)
        
        # Random brightness
        if np.random.random() > 0.5:
            image = self.adjust_brightness(image, np.random.uniform(0.8, 1.2))
        
        # Random contrast
        if np.random.random() > 0.5:
            image = self.adjust_contrast(image, np.random.uniform(0.8, 1.2))
        
        # Random saturation
        if np.random.random() > 0.5:
            image = self.adjust_saturation(image, np.random.uniform(0.8, 1.2))
        
        return image, bboxes
    
    def horizontal_flip(
        self,
        image: np.ndarray,
        bboxes: Optional[List[List[float]]] = None
    ) -> Tuple[np.ndarray, Optional[List[List[float]]]]:
        """Horizontal flip"""
        flipped = cv2.flip(image, 1)
        
        if bboxes is not None:
            w = image.shape[1]
            flipped_bboxes = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                flipped_bboxes.append([w - x2, y1, w - x1, y2])
            return flipped, flipped_bboxes
        
        return flipped, None
    
    def adjust_brightness(self, image: np.ndarray, factor: float) -> np.ndarray:
        """Adjust brightness"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def adjust_contrast(self, image: np.ndarray, factor: float) -> np.ndarray:
        """Adjust contrast"""
        mean = np.mean(image)
        return np.clip((image - mean) * factor + mean, 0, 255).astype(np.uint8)
    
    def adjust_saturation(self, image: np.ndarray, factor: float) -> np.ndarray:
        """Adjust saturation"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def random_crop(
        self,
        image: np.ndarray,
        crop_ratio: float = 0.8
    ) -> np.ndarray:
        """Random crop"""
        h, w = image.shape[:2]
        new_h = int(h * crop_ratio)
        new_w = int(w * crop_ratio)
        
        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)
        
        return image[top:top + new_h, left:left + new_w]


class EdgeOptimizer:
    """Optimize images for edge device inference"""
    
    def __init__(self, target_device: str = "cpu"):
        self.target_device = target_device
    
    def optimize_for_inference(
        self,
        image: np.ndarray,
        quantize: bool = False
    ) -> np.ndarray:
        """
        Optimize image for edge inference.
        
        Args:
            image: Input image
            quantize: Whether to quantize to int8
            
        Returns:
            Optimized image
        """
        # Ensure contiguous memory layout
        image = np.ascontiguousarray(image)
        
        # Quantize if requested
        if quantize:
            image = self._quantize_int8(image)
        
        return image
    
    def _quantize_int8(self, image: np.ndarray) -> np.ndarray:
        """Quantize to int8"""
        if image.dtype == np.float32:
            # Scale to int8 range
            scale = 127.0 / np.max(np.abs(image))
            return (image * scale).astype(np.int8)
        return image.astype(np.int8)
    
    def reduce_resolution(
        self,
        image: np.ndarray,
        scale: float = 0.5
    ) -> np.ndarray:
        """Reduce resolution for faster inference"""
        h, w = image.shape[:2]
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
