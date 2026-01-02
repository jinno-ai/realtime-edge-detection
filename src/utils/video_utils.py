"""
Video Utilities for Real-time Detection

Handles video capture, streaming, and output.
"""

import cv2
import numpy as np
from typing import Generator, Tuple, Optional, Callable
import time
from threading import Thread
from queue import Queue


class VideoCapture:
    """Enhanced video capture with buffering"""
    
    def __init__(
        self,
        source: int | str = 0,
        buffer_size: int = 2,
        fps: Optional[int] = None
    ):
        """
        Initialize video capture.
        
        Args:
            source: Camera index or video file path
            buffer_size: Frame buffer size
            fps: Target FPS (None for source FPS)
        """
        self.source = source
        self.buffer_size = buffer_size
        self.target_fps = fps
        
        self.cap = None
        self.frame_queue = Queue(maxsize=buffer_size)
        self.running = False
        self.thread = None
        
        # Stats
        self.frame_count = 0
        self.start_time = None
    
    def start(self) -> 'VideoCapture':
        """Start video capture"""
        self.cap = cv2.VideoCapture(self.source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {self.source}")
        
        # Set buffer size
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
        
        self.running = True
        self.start_time = time.time()
        
        # Start capture thread
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        return self
    
    def _capture_loop(self):
        """Capture frames in background thread"""
        while self.running:
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Drop old frames if queue is full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
            
            self.frame_queue.put(frame)
            self.frame_count += 1
            
            # FPS limiting
            if self.target_fps:
                time.sleep(1.0 / self.target_fps)
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame"""
        if not self.running:
            return False, None
        
        try:
            frame = self.frame_queue.get(timeout=1.0)
            return True, frame
        except:
            return False, None
    
    def stop(self):
        """Stop video capture"""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        if self.cap:
            self.cap.release()
    
    def get_fps(self) -> float:
        """Get actual FPS"""
        if self.start_time and self.frame_count > 0:
            elapsed = time.time() - self.start_time
            return self.frame_count / elapsed
        return 0.0
    
    @property
    def width(self) -> int:
        """Get frame width"""
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self.cap else 0
    
    @property
    def height(self) -> int:
        """Get frame height"""
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self.cap else 0
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, *args):
        self.stop()


class VideoWriter:
    """Video writer with codec support"""
    
    def __init__(
        self,
        output_path: str,
        fps: float = 30.0,
        frame_size: Optional[Tuple[int, int]] = None,
        codec: str = 'mp4v'
    ):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.codec = codec
        self.writer = None
    
    def start(self, frame_size: Optional[Tuple[int, int]] = None) -> 'VideoWriter':
        """Start video writer"""
        size = frame_size or self.frame_size
        
        if size is None:
            raise ValueError("Frame size must be specified")
        
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, size)
        
        if not self.writer.isOpened():
            raise RuntimeError(f"Failed to create video writer: {self.output_path}")
        
        return self
    
    def write(self, frame: np.ndarray):
        """Write a frame"""
        if self.writer is None:
            # Auto-start with frame size
            h, w = frame.shape[:2]
            self.start((w, h))
        
        self.writer.write(frame)
    
    def stop(self):
        """Stop video writer"""
        if self.writer:
            self.writer.release()
            self.writer = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.stop()


class FrameProcessor:
    """Process video frames with detection"""
    
    def __init__(
        self,
        detector: Callable,
        display: bool = True,
        save_output: Optional[str] = None
    ):
        self.detector = detector
        self.display = display
        self.save_output = save_output
        
        self.writer = None
        self.fps_history = []
    
    def process_video(
        self,
        source: int | str = 0,
        max_frames: Optional[int] = None
    ) -> dict:
        """
        Process video with detection.
        
        Args:
            source: Video source
            max_frames: Maximum frames to process
            
        Returns:
            Processing statistics
        """
        cap = VideoCapture(source)
        cap.start()
        
        if self.save_output:
            self.writer = VideoWriter(self.save_output)
        
        frame_count = 0
        total_inference_time = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                if max_frames and frame_count >= max_frames:
                    break
                
                # Run detection
                start_time = time.time()
                detections = self.detector(frame)
                inference_time = time.time() - start_time
                
                total_inference_time += inference_time
                fps = 1.0 / inference_time if inference_time > 0 else 0
                self.fps_history.append(fps)
                
                # Draw detections
                annotated = self._draw_detections(frame, detections, fps)
                
                # Display
                if self.display:
                    cv2.imshow('Detection', annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Save
                if self.writer:
                    self.writer.write(annotated)
                
                frame_count += 1
        
        finally:
            cap.stop()
            if self.writer:
                self.writer.stop()
            if self.display:
                cv2.destroyAllWindows()
        
        # Calculate stats
        avg_fps = frame_count / total_inference_time if total_inference_time > 0 else 0
        
        return {
            'frames_processed': frame_count,
            'total_time': total_inference_time,
            'average_fps': avg_fps,
            'min_fps': min(self.fps_history) if self.fps_history else 0,
            'max_fps': max(self.fps_history) if self.fps_history else 0
        }
    
    def _draw_detections(
        self,
        frame: np.ndarray,
        detections: list,
        fps: float
    ) -> np.ndarray:
        """Draw detections on frame"""
        annotated = frame.copy()
        
        # Draw bounding boxes
        for det in detections:
            bbox = det.get('bbox', [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                
                # Draw box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"{det.get('class_name', 'object')}: {det.get('confidence', 0):.2f}"
                cv2.putText(
                    annotated, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                )
        
        # Draw FPS
        cv2.putText(
            annotated, f"FPS: {fps:.1f}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
        
        return annotated


def stream_frames(source: int | str = 0) -> Generator[np.ndarray, None, None]:
    """Generator for streaming frames"""
    cap = cv2.VideoCapture(source)
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
    finally:
        cap.release()
