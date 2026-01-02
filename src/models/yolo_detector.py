"""
YOLO Object Detector

Real-time object detection using YOLO v8.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Union
import time
import warnings

from ..config.config_manager import ConfigManager


class YOLODetector:
    """YOLO v8 object detector for edge devices"""

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        config: Optional[Union[ConfigManager, str]] = None
    ):
        """
        Initialize YOLO detector.

        Args:
            model_path: Path to model file (deprecated, use config)
            conf_threshold: Confidence threshold (deprecated, use config)
            iou_threshold: IOU threshold (deprecated, use config)
            config: ConfigManager instance or path to config file

        Examples:
            # New usage with config
            detector = YOLODetector(config='config.yaml')
            detector = YOLODetector(config=ConfigManager(profile='prod'))

            # Legacy usage (deprecated, shows warning)
            detector = YOLODetector(model_path='yolov8n.pt', conf_threshold=0.5)
        """
        # Initialize configuration
        if config is None and model_path is None:
            # Use default config
            self.config = ConfigManager()
        elif isinstance(config, str):
            # Config path provided
            self.config = ConfigManager(config_path=config)
        elif isinstance(config, ConfigManager):
            # ConfigManager instance provided
            self.config = config
        else:
            # Legacy mode - create default config and issue warning
            self.config = ConfigManager()
            if model_path is not None:
                warnings.warn(
                    "Initializing YOLODetector with model_path parameter is deprecated. "
                    "Use ConfigManager instead. Example: YOLODetector(config='config.yaml')",
                    DeprecationWarning,
                    stacklevel=2
                )
                # Override config with legacy parameters
                self.config.config['model']['path'] = model_path
            if conf_threshold is not None:
                self.config.config['detection']['confidence_threshold'] = conf_threshold
            if iou_threshold is not None:
                self.config.config['detection']['iou_threshold'] = iou_threshold

        # Load configuration values
        self.model_path = self.config.get('model', 'path')
        self.conf_threshold = self.config.get('detection', 'confidence_threshold')
        self.iou_threshold = self.config.get('detection', 'iou_threshold')
        self.max_detections = self.config.get('detection', 'max_detections')

        self.model = None
        self.class_names = []
    
    def load_model(self) -> None:
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"✅ Model loaded: {self.model_path}")
        except ImportError:
            print("⚠️  ultralytics not installed. Run: pip install ultralytics")
            raise
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects in image.

        Args:
            image: Input image (numpy array)

        Returns:
            List of detections, each containing bbox, confidence, class_id, class_name
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Run inference
        results = self.model(image, conf=self.conf_threshold, iou=self.iou_threshold)

        # Parse results
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())

                detections.append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'class_id': cls,
                    'class_name': self.model.names[cls]
                })

                # Limit to max_detections
                if len(detections) >= self.max_detections:
                    break

        return detections
    
    def detect_video(self, video_path: str, output_path: str = None) -> None:
        """Detect objects in video"""
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Video writer
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        total_time = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect
            start_time = time.time()
            detections = self.detect(frame)
            inference_time = time.time() - start_time
            
            # Draw detections
            frame = self.draw_detections(frame, detections)
            
            # Add FPS
            fps_text = f"FPS: {1/inference_time:.1f}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if writer:
                writer.write(frame)
            
            frame_count += 1
            total_time += inference_time
        
        cap.release()
        if writer:
            writer.release()
        
        avg_fps = frame_count / total_time if total_time > 0 else 0
        print(f"✅ Processed {frame_count} frames")
        print(f"   Average FPS: {avg_fps:.1f}")
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Draw bounding boxes on image"""
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            
            # Draw box
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return image
