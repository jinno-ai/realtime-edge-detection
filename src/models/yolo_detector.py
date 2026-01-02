"""
YOLO Object Detector

Real-time object detection using YOLO v8.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import time


class YOLODetector:
    """YOLO v8 object detector for edge devices"""
    
    def __init__(self, model_path: str, conf_threshold: float = 0.5, iou_threshold: float = 0.4):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
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
        """Detect objects in image"""
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
