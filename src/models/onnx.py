"""
ONNX Runtime detector implementation.

Provides ONNX Runtime-based object detection with optimized performance.
"""

import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from .base import AbstractDetector


class ONNXDetector(AbstractDetector):
    """
    ONNX Runtime detector implementation.

    Features:
    - CPU and GPU inference via ONNX Runtime
    - Fast model loading
    - Low memory footprint
    - Compatible with ONNX-converted YOLO models
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ONNX detector.

        Args:
            config: Configuration dictionary
                - model_path: Path to ONNX model file
                - device: 'cpu' or 'cuda'
                - provider: ONNX Runtime provider (default: auto)
                - confidence_threshold: Detection confidence threshold
                - iou_threshold: NMS IOU threshold
        """
        super().__init__(config)

        self.model_path = config.get('model_path')
        self.device = config.get('device', 'cpu')
        self.provider = config.get('provider', None)
        self.confidence_threshold = config.get('confidence_threshold', 0.25)
        self.iou_threshold = config.get('iou_threshold', 0.45)

        # ONNX Runtime session
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None

        # Class names (COCO dataset)
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]

    def load_model(self) -> None:
        """
        Load ONNX model with ONNX Runtime.

        Raises:
            RuntimeError: If model loading fails
        """
        try:
            import onnxruntime as ort

            if not Path(self.model_path).exists():
                raise RuntimeError(f"Model file not found: {self.model_path}")

            # Determine provider
            if self.provider is None:
                # Auto-select provider based on device
                if self.device == 'cuda' and 'CUDAExecutionProvider' in ort.get_available_providers():
                    self.provider = 'CUDAExecutionProvider'
                else:
                    self.provider = 'CPUExecutionProvider'

            # Create inference session
            print(f"🔧 Loading ONNX model: {self.model_path}")
            print(f"   Provider: {self.provider}")

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=sess_options,
                providers=[self.provider]
            )

            # Get input/output info
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape

            print(f"   Input shape: {self.input_shape}")
            print(f"   Outputs: {self.output_names}")
            print("✅ Model loaded successfully")

        except ImportError:
            raise RuntimeError(
                "ONNX Runtime not installed. Install with: pip install onnxruntime"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")

    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on a single image.

        Args:
            image: Input image as numpy array (BGR format)

        Returns:
            List of detection dictionaries
        """
        if self.session is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Preprocess
        processed = self.preprocess(image)

        # Run inference
        outputs = self.session.run(
            self.output_names,
            {self.input_name: processed}
        )

        # Postprocess
        detections = self.postprocess(outputs[0], image.shape)

        return detections

    def detect_batch(self, images: List[np.ndarray]) -> List[List[Dict[str, Any]]]:
        """
        Run detection on a batch of images.

        Args:
            images: List of input images

        Returns:
            List of detection lists
        """
        if self.session is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        results = []
        for image in images:
            detections = self.detect(image)
            results.append(detections)

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata.

        Returns:
            Dictionary with model information
        """
        return {
            'name': Path(self.model_path).stem,
            'version': 'onnx',
            'classes': self.class_names,
            'input_size': (
                self.input_shape[3] if self.input_shape[3] else 640,
                self.input_shape[2] if self.input_shape[2] else 640
            ),
            'provider': self.provider,
            'num_params': None,  # ONNX doesn't expose parameter count easily
            'model_path': self.model_path
        }

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for ONNX model.

        Args:
            image: Input image (BGR, HWC)

        Returns:
            Preprocessed tensor (1, 3, H, W)
        """
        import cv2

        # Get target size from input shape
        if self.input_shape and len(self.input_shape) == 4:
            target_height = self.input_shape[2] if self.input_shape[2] else 640
            target_width = self.input_shape[3] if self.input_shape[3] else 640
        else:
            target_height = 640
            target_width = 640

        # Resize with letterbox
        img = self._letterbox(image, (target_width, target_height))

        # Convert HWC to CHW
        img = img.transpose(2, 0, 1)

        # Normalize to 0-1
        img = img.astype(np.float32) / 255.0

        # Add batch dimension
        img = np.expand_dims(img, axis=0)

        return img

    def postprocess(
        self,
        raw_output: np.ndarray,
        original_shape: tuple
    ) -> List[Dict[str, Any]]:
        """
        Postprocess raw model output to detections.

        Args:
            raw_output: Raw output from model
            original_shape: Original image shape (H, W, C)

        Returns:
            List of detection dictionaries
        """
        detections = []

        # Transpose output if needed: (1, 84, 8400) -> (8400, 84)
        if raw_output.ndim == 3 and raw_output.shape[0] == 1:
            raw_output = raw_output[0]  # Remove batch dim
        if raw_output.shape[0] < raw_output.shape[1]:
            raw_output = raw_output.T

        # Extract boxes and scores
        # Format: [x, y, w, h, conf, class1, class2, ...]
        boxes = raw_output[:, :4]
        obj_conf = raw_output[:, 4]
        class_probs = raw_output[:, 5:]

        # Calculate final confidence scores
        class_confs = obj_conf[:, np.newaxis] * class_probs

        # Get best class for each detection
        max_confs = np.max(class_confs, axis=1)
        max_classes = np.argmax(class_confs, axis=1)

        # Filter by confidence threshold
        mask = max_confs > self.confidence_threshold
        boxes = boxes[mask]
        max_confs = max_confs[mask]
        max_classes = max_classes[mask]

        # Convert center format to corner format
        if len(boxes) > 0:
            x_center = boxes[:, 0]
            y_center = boxes[:, 1]
            width = boxes[:, 2]
            height = boxes[:, 3]

            x1 = x_center - width / 2
            y1 = y_center - height / 2
            x2 = x_center + width / 2
            y2 = y_center + height / 2

            # Scale to original image size
            orig_h, orig_w = original_shape[:2]
            scale = max(orig_w, orig_h) / 640  # Assuming 640 model input

            x1 = (x1 * scale).astype(int)
            y1 = (y1 * scale).astype(int)
            x2 = (x2 * scale).astype(int)
            y2 = (y2 * scale).astype(int)

            # Clamp to image bounds
            x1 = np.clip(x1, 0, orig_w)
            y1 = np.clip(y1, 0, orig_h)
            x2 = np.clip(x2, 0, orig_w)
            y2 = np.clip(y2, 0, orig_h)

            # Create detection list
            for i in range(len(boxes)):
                if max_classes[i] < len(self.class_names):
                    detections.append({
                        'class': self.class_names[max_classes[i]],
                        'confidence': float(max_confs[i]),
                        'bbox': [int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])]
                    })

        return detections

    def _letterbox(
        self,
        img: np.ndarray,
        target_size: tuple,
        color: tuple = (114, 114, 114)
    ) -> np.ndarray:
        """
        Resize image with letterbox (maintain aspect ratio).

        Args:
            img: Input image
            target_size: Target (width, height)
            color: Padding color

        Returns:
            Resized and padded image
        """
        import cv2

        target_w, target_h = target_size
        h, w = img.shape[:2]

        # Calculate scale
        scale = min(target_w / w, target_h / h)

        # Calculate new size
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Resize
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Create padded image
        padded = np.full((target_h, target_w, 3), color, dtype=np.uint8)

        # Calculate padding
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2

        # Place resized image
        padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        return padded
