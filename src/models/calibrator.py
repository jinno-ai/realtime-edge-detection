"""
Calibration dataset handler for INT8 quantization.

Manages download and preparation of calibration data for static quantization.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
import urllib.request
import zipfile

import numpy as np
import cv2


class Calibrator:
    """
    Calibration dataset handler for INT8 quantization.
    
    Downloads and prepares representative data for static INT8 calibration.
    """
    
    CALIBRATION_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"
    CALIBRATION_SIZE = 100  # Number of images for calibration
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize calibrator.
        
        Args:
            cache_dir: Cache directory for calibration data
        """
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'edge-detection' / 'calibration'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_calibration_data(
        self,
        num_images: int = CALIBRATION_SIZE,
        force_download: bool = False
    ) -> List[np.ndarray]:
        """
        Get calibration dataset.
        
        Downloads COCO128 subset if not available.
        
        Args:
            num_images: Number of calibration images to return
            force_download: Force re-download even if data exists
            
        Returns:
            List of calibration images as numpy arrays
        """
        calibration_path = self.cache_dir / 'coco128'
        
        # Download if needed
        if not calibration_path.exists() or force_download:
            print("📥 Downloading calibration dataset (COCO128)...")
            self._download_calibration_dataset(calibration_path)
            print("✅ Calibration dataset downloaded")
        
        # Load calibration images
        images = self._load_calibration_images(calibration_path, num_images)
        
        print(f"📊 Loaded {len(images)} calibration images")
        
        return images
    
    def _download_calibration_dataset(self, target_path: Path) -> None:
        """
        Download and extract calibration dataset.
        
        Args:
            target_path: Target directory for extraction
        """
        zip_path = self.cache_dir / 'coco128.zip'
        
        # Download
        print(f"   Downloading from {self.CALIBRATION_URL}...")
        urllib.request.urlretrieve(self.CALIBRATION_URL, zip_path)
        
        # Extract
        print("   Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.cache_dir)
        
        # Clean up zip
        zip_path.unlink()
    
    def _load_calibration_images(
        self,
        dataset_path: Path,
        num_images: int
    ) -> List[np.ndarray]:
        """
        Load calibration images from dataset.
        
        Args:
            dataset_path: Path to dataset
            num_images: Number of images to load
            
        Returns:
            List of images as numpy arrays
        """
        images = []
        
        # COCO128 structure: images/train2017/*.jpg
        images_dir = dataset_path / 'images' / 'train2017'
        
        if not images_dir.exists():
            # Try alternative structure
            images_dir = dataset_path / 'images'
        
        # Get image files
        image_files = sorted(images_dir.glob('*.jpg'))[:num_images]
        
        if not image_files:
            raise FileNotFoundError(
                f"No images found in {images_dir}. "
                f"Please check calibration dataset structure."
            )
        
        # Load images
        for img_path in image_files:
            img = cv2.imread(str(img_path))
            if img is not None:
                images.append(img)
        
        return images
    
    def prepare_calibration_tensors(
        self,
        images: List[np.ndarray],
        input_size: Tuple[int, int] = (640, 640)
    ) -> List[torch.Tensor]:
        """
        Prepare calibration images as tensors.
        
        Args:
            images: List of images as numpy arrays
            input_size: Target input size (width, height)
            
        Returns:
            List of prepared tensors
        """
        import torch
        
        tensors = []
        
        for img in images:
            # Resize
            img_resized = cv2.resize(img, input_size)
            
            # Convert to tensor
            img_tensor = torch.from_numpy(img_resized).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
            
            tensors.append(img_tensor)
        
        return tensors
