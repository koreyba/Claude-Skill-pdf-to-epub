"""Tests for ImageOptimizer."""

import pytest
from io import BytesIO
from PIL import Image

from claude_skill.core.image_optimizer import ImageOptimizer, ImageOptimizationConfig
from claude_skill.conversion.models import ImageResource


class TestImageOptimizer:
    """Test ImageOptimizer class."""

    def _create_test_image(self, width: int, height: int, mode: str = 'RGB') -> bytes:
        """Create a test image."""
        img = Image.new(mode, (width, height), color='red')
        buffer = BytesIO()
        fmt = 'PNG' if mode == 'RGBA' else 'JPEG'
        img.save(buffer, format=fmt)
        return buffer.getvalue()

    def _create_image_resource(
        self,
        width: int = 100,
        height: int = 100,
        mode: str = 'RGB',
        format: str = 'jpeg'
    ) -> ImageResource:
        """Create a test ImageResource."""
        data = self._create_test_image(width, height, mode)
        return ImageResource(
            id="test",
            filename=f"test.{format}",
            data=data,
            format=format,
            width=width,
            height=height,
            page_num=1
        )

    def test_resize_large_image(self):
        """Images larger than max dimensions are resized."""
        config = ImageOptimizationConfig(max_width=100, max_height=100)
        optimizer = ImageOptimizer(config)

        resource = self._create_image_resource(width=2000, height=1500)
        result = optimizer.optimize(resource)

        assert result.width <= 100
        # Aspect ratio preserved: 2000/1500 = 100/75
        assert result.height <= 100

    def test_small_image_not_resized(self):
        """Images within max dimensions are not resized."""
        config = ImageOptimizationConfig(max_width=1200, max_height=1600)
        optimizer = ImageOptimizer(config)

        resource = self._create_image_resource(width=500, height=400)
        result = optimizer.optimize(resource)

        assert result.width == 500
        assert result.height == 400

    def test_aspect_ratio_preserved(self):
        """Aspect ratio is preserved when resizing."""
        config = ImageOptimizationConfig(max_width=100, max_height=200)
        optimizer = ImageOptimizer(config)

        # Create a 400x200 image (2:1 ratio)
        resource = self._create_image_resource(width=400, height=200)
        result = optimizer.optimize(resource)

        # Should be scaled to 100x50 (limited by width)
        assert result.width == 100
        assert result.height == 50

    def test_rgba_to_rgb_conversion(self):
        """RGBA images without actual transparency are converted to RGB for JPEG output."""
        config = ImageOptimizationConfig(convert_png_to_jpeg=True)
        optimizer = ImageOptimizer(config)

        # Create RGBA image (PNG) with fully opaque pixels (alpha=255)
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        resource = ImageResource(
            id="test",
            filename="test.png",
            data=buffer.getvalue(),
            format="png",
            width=100,
            height=100,
            page_num=1
        )

        result = optimizer.optimize(resource)

        # Should be converted to JPEG (no actual transparency)
        assert result.format in ['jpeg', 'jpg']
        assert result.filename.endswith('.jpg')

    def test_png_with_transparency_stays_png(self):
        """PNG with actual transparency stays as PNG."""
        config = ImageOptimizationConfig(convert_png_to_jpeg=True)
        optimizer = ImageOptimizer(config)

        # Create RGBA image with actual transparency (alpha < 255)
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 0))  # Fully transparent
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        resource = ImageResource(
            id="test",
            filename="test.png",
            data=buffer.getvalue(),
            format="png",
            width=100,
            height=100,
            page_num=1
        )

        result = optimizer.optimize(resource)

        # Should stay PNG due to transparency
        assert result.format == 'png'

    def test_jpeg_compression(self):
        """JPEG images are compressed with configured quality."""
        # Create a large uncompressed-like image
        img = Image.new('RGB', (500, 500), color='red')
        # Add some variation to prevent extreme compression
        for x in range(0, 500, 10):
            for y in range(0, 500, 10):
                img.putpixel((x, y), (x % 256, y % 256, 128))

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=100)
        original_data = buffer.getvalue()

        resource = ImageResource(
            id="test",
            filename="test.jpg",
            data=original_data,
            format="jpeg",
            width=500,
            height=500,
            page_num=1
        )

        config = ImageOptimizationConfig(jpeg_quality=50)
        optimizer = ImageOptimizer(config)
        result = optimizer.optimize(resource)

        # Compressed size should be smaller (or at least different)
        assert len(result.data) != len(original_data)

    def test_batch_optimization(self):
        """Batch optimization processes all images."""
        optimizer = ImageOptimizer()

        resources = [
            self._create_image_resource(width=100 + i * 10, height=100 + i * 10)
            for i in range(3)
        ]

        results = optimizer.optimize_batch(resources)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.id == "test"

    def test_empty_batch(self):
        """Empty batch returns empty list."""
        optimizer = ImageOptimizer()
        results = optimizer.optimize_batch([])
        assert results == []

    def test_gif_stays_gif(self):
        """GIF images stay as GIF (for animations)."""
        config = ImageOptimizationConfig(convert_png_to_jpeg=True)
        optimizer = ImageOptimizer(config)

        img = Image.new('P', (100, 100), color=1)
        buffer = BytesIO()
        img.save(buffer, format='GIF')

        resource = ImageResource(
            id="test",
            filename="test.gif",
            data=buffer.getvalue(),
            format="gif",
            width=100,
            height=100,
            page_num=1
        )

        result = optimizer.optimize(resource)
        assert result.format == 'gif'

    def test_default_config(self):
        """Default config has reasonable values."""
        config = ImageOptimizationConfig()

        assert config.enabled is True
        assert config.max_width == 1200
        assert config.max_height == 1600
        assert config.jpeg_quality == 85
        assert config.convert_png_to_jpeg is False

    def test_filename_extension_updated(self):
        """Filename extension is updated when format changes."""
        config = ImageOptimizationConfig(convert_png_to_jpeg=True)
        optimizer = ImageOptimizer(config)

        # Create opaque PNG (no transparency)
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        resource = ImageResource(
            id="test",
            filename="image001.png",
            data=buffer.getvalue(),
            format="png",
            width=100,
            height=100,
            page_num=1
        )

        result = optimizer.optimize(resource)

        # Should be converted to JPEG with updated filename
        assert result.filename == "image001.jpg"
        assert result.format in ['jpeg', 'jpg']


class TestImageOptimizationConfig:
    """Test ImageOptimizationConfig dataclass."""

    def test_default_values(self):
        """Config has sensible defaults."""
        config = ImageOptimizationConfig()

        assert config.enabled is True
        assert config.max_width == 1200
        assert config.max_height == 1600
        assert config.jpeg_quality == 85
        assert config.convert_png_to_jpeg is False
        assert config.jpeg_background_color == (255, 255, 255)

    def test_custom_values(self):
        """Config accepts custom values."""
        config = ImageOptimizationConfig(
            enabled=False,
            max_width=800,
            max_height=1000,
            jpeg_quality=70,
            convert_png_to_jpeg=True,
            jpeg_background_color=(200, 200, 200)
        )

        assert config.enabled is False
        assert config.max_width == 800
        assert config.max_height == 1000
        assert config.jpeg_quality == 70
        assert config.convert_png_to_jpeg is True
        assert config.jpeg_background_color == (200, 200, 200)
