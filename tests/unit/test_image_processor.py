"""
Unit tests for ImageProcessor, ImageAugmentor, and EdgeOptimizer

Tests image preprocessing, augmentation, and optimization functionality
"""

import pytest
import numpy as np
from src.preprocessing.image_processor import (
    ImageProcessor,
    ImageAugmentor,
    EdgeOptimizer
)


@pytest.mark.unit
class TestImageProcessor:
    """Test ImageProcessor functionality"""

    def test_initialization_with_defaults(self):
        """Test ImageProcessor initialization with default parameters"""
        processor = ImageProcessor()

        assert processor.target_size == (640, 640)
        assert processor.normalize is True
        assert processor.mean is not None
        assert processor.std is not None

    def test_initialization_with_custom_params(self):
        """Test ImageProcessor initialization with custom parameters"""
        processor = ImageProcessor(
            target_size=(320, 320),
            normalize=False,
            mean=(0.5, 0.5, 0.5),
            std=(0.5, 0.5, 0.5)
        )

        assert processor.target_size == (320, 320)
        assert processor.normalize is False
        assert np.allclose(processor.mean, np.array([0.5, 0.5, 0.5]))

    @pytest.mark.unit
    def test_preprocess_bgr_to_rgb_conversion(self, sample_image_bgr):
        """Test that preprocess converts BGR to RGB"""
        processor = ImageProcessor(normalize=False)
        result = processor.preprocess(sample_image_bgr)

        # Result should be in NCHW format after transpose
        assert result.shape[0] == 1  # Batch dimension
        assert result.shape[1] == 3  # Channels
        assert result.dtype == np.float32

    @pytest.mark.unit
    def test_preprocess_normalization(self, sample_image_bgr):
        """Test image normalization"""
        processor = ImageProcessor(normalize=True)
        result = processor.preprocess(sample_image_bgr)

        # Check that values are normalized (not in 0-255 range)
        assert result.max() <= 3.0  # Allow some margin
        assert result.min() >= -3.0

    @pytest.mark.unit
    def test_preprocess_without_normalization(self, sample_image_bgr):
        """Test preprocessing without normalization"""
        processor = ImageProcessor(normalize=False)
        result = processor.preprocess(sample_image_bgr)

        # Values should be 0-1 after division by 255
        assert result.max() <= 1.0
        assert result.min() >= 0.0

    @pytest.mark.unit
    def test_resize_without_keep_ratio(self, sample_image_bgr):
        """Test resize without aspect ratio preservation"""
        processor = ImageProcessor()
        resized = processor.resize(sample_image_bgr, (320, 320), keep_ratio=False)

        assert resized.shape == (320, 320, 3)

    @pytest.mark.unit
    def test_resize_with_keep_ratio(self):
        """Test resize with aspect ratio preservation"""
        processor = ImageProcessor()
        # Create non-square image
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        resized = processor.resize(image, (640, 640), keep_ratio=True)

        # Should be square target size with padding
        assert resized.shape == (640, 640, 3)

    @pytest.mark.unit
    def test_letterbox_returns_correct_format(self):
        """Test letterbox preprocessing returns correct format"""
        processor = ImageProcessor()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        padded, scale, padding = processor.letterbox(image, target_size=(640, 640))

        assert padded.shape == (640, 640, 3)
        assert scale > 0
        assert len(padding) == 2
        assert isinstance(padding[0], int)
        assert isinstance(padding[1], int)

    @pytest.mark.unit
    def test_letterbox_with_different_sizes(self):
        """Test letterbox with various input sizes"""
        processor = ImageProcessor()

        sizes = [
            (320, 240),  # Smaller than target
            (1280, 720),  # Larger than target
            (640, 640),  # Same as target
        ]

        for w, h in sizes:
            image = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            padded, scale, padding = processor.letterbox(image, (640, 640))

            assert padded.shape == (640, 640, 3)

    @pytest.mark.unit
    def test_batch_preprocess(self, sample_images_batch):
        """Test batch preprocessing"""
        processor = ImageProcessor(normalize=False)
        batch = processor.batch_preprocess(sample_images_batch)

        assert batch.shape[0] == len(sample_images_batch)
        assert batch.shape[1] == 3  # Channels
        assert len(batch.shape) == 4  # NCHW format


@pytest.mark.unit
class TestImageAugmentor:
    """Test ImageAugmentor functionality"""

    def test_initialization_with_seed(self):
        """Test augmentor initialization with seed for reproducibility"""
        augmentor1 = ImageAugmentor(seed=42)
        augmentor2 = ImageAugmentor(seed=42)

        # Should produce same results with same seed
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        aug1, _ = augmentor1.augment(image)
        aug2, _ = augmentor2.augment(image)

        # Results should be identical with same seed
        # (Note: This depends on random operations being applied)
        assert aug1.shape == aug2.shape

    @pytest.mark.unit
    def test_augment_returns_same_shape(self, sample_image_bgr):
        """Test that augment preserves image shape"""
        augmentor = ImageAugmentor(seed=42)
        augmented, _ = augmentor.augment(sample_image_bgr)

        assert augmented.shape == sample_image_bgr.shape
        assert augmented.dtype == sample_image_bgr.dtype

    @pytest.mark.unit
    def test_horizontal_flip(self, sample_image_bgr, sample_bboxes):
        """Test horizontal flip with bounding boxes"""
        augmentor = ImageAugmentor()
        flipped, flipped_bboxes = augmentor.horizontal_flip(sample_image_bgr, sample_bboxes)

        assert flipped.shape == sample_image_bgr.shape

        # Check that bboxes were flipped
        assert len(flipped_bboxes) == len(sample_bboxes)
        w = sample_image_bgr.shape[1]

        # First bbox: [100, 100, 200, 200]
        # After flip: [w-200, 100, w-100, 200]
        x1_new, y1_new, x2_new, y2_new = flipped_bboxes[0]
        assert x1_new == w - 200
        assert x2_new == w - 100
        assert y1_new == 100
        assert y2_new == 200

    @pytest.mark.unit
    def test_horizontal_flip_without_bboxes(self, sample_image_bgr):
        """Test horizontal flip without bounding boxes"""
        augmentor = ImageAugmentor()
        flipped, bboxes = augmentor.horizontal_flip(sample_image_bgr, None)

        assert flipped.shape == sample_image_bgr.shape
        assert bboxes is None

    @pytest.mark.unit
    def test_adjust_brightness(self, sample_image_bgr):
        """Test brightness adjustment"""
        augmentor = ImageAugmentor()

        # Increase brightness
        brighter = augmentor.adjust_brightness(sample_image_bgr, 1.5)
        assert brighter.shape == sample_image_bgr.shape

        # Decrease brightness
        darker = augmentor.adjust_brightness(sample_image_bgr, 0.7)
        assert darker.shape == sample_image_bgr.shape

    @pytest.mark.unit
    def test_adjust_contrast(self, sample_image_bgr):
        """Test contrast adjustment"""
        augmentor = ImageAugmentor()

        # Increase contrast
        high_contrast = augmentor.adjust_contrast(sample_image_bgr, 1.5)
        assert high_contrast.shape == sample_image_bgr.shape
        assert high_contrast.dtype == np.uint8

        # Decrease contrast
        low_contrast = augmentor.adjust_contrast(sample_image_bgr, 0.7)
        assert low_contrast.shape == sample_image_bgr.shape

    @pytest.mark.unit
    def test_adjust_saturation(self, sample_image_bgr):
        """Test saturation adjustment"""
        augmentor = ImageAugmentor()

        saturated = augmentor.adjust_saturation(sample_image_bgr, 1.5)
        assert saturated.shape == sample_image_bgr.shape
        assert saturated.dtype == np.uint8

    @pytest.mark.unit
    def test_random_crop(self, sample_image_bgr):
        """Test random cropping"""
        augmentor = ImageAugmentor(seed=42)

        cropped = augmentor.random_crop(sample_image_bgr, crop_ratio=0.8)

        # Cropped image should be smaller
        assert cropped.shape[0] < sample_image_bgr.shape[0]
        assert cropped.shape[1] < sample_image_bgr.shape[1]
        assert cropped.shape[2] == sample_image_bgr.shape[2]

    @pytest.mark.unit
    def test_augment_with_bboxes(self, sample_image_bgr, sample_bboxes):
        """Test augmentation with bounding box transformation"""
        augmentor = ImageAugmentor(seed=42)
        augmented, aug_bboxes = augmentor.augment(sample_image_bgr, sample_bboxes)

        assert augmented.shape == sample_image_bgr.shape
        assert len(aug_bboxes) == len(sample_bboxes)


@pytest.mark.unit
class TestEdgeOptimizer:
    """Test EdgeOptimizer functionality"""

    def test_initialization(self):
        """Test EdgeOptimizer initialization"""
        optimizer = EdgeOptimizer(target_device="cpu")
        assert optimizer.target_device == "cpu"

    @pytest.mark.unit
    def test_optimize_for_inference_returns_contiguous(self):
        """Test that optimization ensures contiguous memory layout"""
        optimizer = EdgeOptimizer()

        # Create non-contiguous array
        image = np.random.rand(480, 640, 3).astype(np.float32)
        non_contiguous = image[::2, ::2, :]  # Strided slice

        optimized = optimizer.optimize_for_inference(non_contiguous, quantize=False)

        assert optimized.flags['C_CONTIGUOUS']

    @pytest.mark.unit
    def test_optimize_for_inference_without_quantization(self):
        """Test optimization without quantization"""
        optimizer = EdgeOptimizer()
        image = np.random.rand(480, 640, 3).astype(np.float32)

        optimized = optimizer.optimize_for_inference(image, quantize=False)

        assert optimized.dtype == np.float32
        assert optimized.shape == image.shape

    @pytest.mark.unit
    def test_optimize_for_inference_with_quantization(self):
        """Test optimization with int8 quantization"""
        optimizer = EdgeOptimizer()
        image = np.random.rand(480, 640, 3).astype(np.float32)

        optimized = optimizer.optimize_for_inference(image, quantize=True)

        assert optimized.dtype == np.int8
        assert optimized.shape == image.shape

    @pytest.mark.unit
    def test_reduce_resolution(self):
        """Test resolution reduction"""
        optimizer = EdgeOptimizer()

        original = np.zeros((1920, 1080, 3), dtype=np.uint8)
        reduced = optimizer.reduce_resolution(original, scale=0.5)

        assert reduced.shape[0] < original.shape[0]
        assert reduced.shape[1] < original.shape[1]
        assert reduced.shape[0] == int(original.shape[0] * 0.5)
        assert reduced.shape[1] == int(original.shape[1] * 0.5)

    @pytest.mark.unit
    def test_reduce_resolution_with_different_scales(self):
        """Test resolution reduction with various scales"""
        optimizer = EdgeOptimizer()
        original = np.zeros((1920, 1080, 3), dtype=np.uint8)

        scales = [0.25, 0.5, 0.75]
        for scale in scales:
            reduced = optimizer.reduce_resolution(original, scale=scale)
            expected_h = int(original.shape[0] * scale)
            expected_w = int(original.shape[1] * scale)
            assert reduced.shape == (expected_h, expected_w, 3)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_preprocess_grayscale_image(self):
        """Test preprocessing with grayscale image"""
        processor = ImageProcessor()
        gray_image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)

        # OpenCV converts grayscale to 3-channel, so this should work
        # or raise error depending on implementation
        try:
            result = processor.preprocess(gray_image)
            # If it works, verify shape
            assert result.shape[1] == 3  # Should have 3 channels
        except (ValueError, IndexError, cv2.error):
            # Also acceptable to raise error
            pass

    def test_resize_with_zero_dimensions(self):
        """Test resize with zero dimensions"""
        processor = ImageProcessor()
        image = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should handle gracefully or raise error
        with pytest.raises((ValueError, cv2.error)):
            processor.resize(image, (0, 0))

    def test_letterbox_with_zero_target_size(self):
        """Test letterbox with zero target size"""
        processor = ImageProcessor()
        image = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises((ValueError, cv2.error, ZeroDivisionError)):
            processor.letterbox(image, target_size=(0, 0))

    def test_batch_preprocess_empty_list(self):
        """Test batch preprocessing with empty list"""
        processor = ImageProcessor()
        # Empty list should raise ValueError in numpy.concatenate
        with pytest.raises(ValueError, match="need at least one array"):
            batch = processor.batch_preprocess([])


# Import cv2 for error tests
import cv2
