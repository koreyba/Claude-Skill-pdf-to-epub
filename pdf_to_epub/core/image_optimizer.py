"""Image optimization for EPUB generation."""

from io import BytesIO
from dataclasses import dataclass
from typing import Optional, Tuple, List

from PIL import Image

from conversion.models import ImageResource
from .utils import get_logger

logger = get_logger(__name__)


@dataclass
class ImageOptimizationConfig:
    """Configuration for image optimization."""
    enabled: bool = True
    max_width: int = 1200
    max_height: int = 1600
    jpeg_quality: int = 85
    convert_png_to_jpeg: bool = False
    jpeg_background_color: Tuple[int, int, int] = (255, 255, 255)  # White


class ImageOptimizer:
    """
    Optimizes images for EPUB output.

    - Resizes to max dimensions while preserving aspect ratio
    - Converts RGBA to RGB with white background for JPEG
    - Compresses JPEG with configurable quality
    - Optionally converts PNG to JPEG for smaller size
    """

    def __init__(self, config: Optional[ImageOptimizationConfig] = None):
        """
        Initialize optimizer with configuration.

        Args:
            config: Optimization settings. Uses defaults if None.
        """
        self.config = config or ImageOptimizationConfig()

    def optimize(self, image_resource: ImageResource) -> ImageResource:
        """
        Optimize an image resource.

        Args:
            image_resource: Original image data

        Returns:
            New ImageResource with optimized data
        """
        try:
            # Load image from bytes
            img = Image.open(BytesIO(image_resource.data))
            original_format = image_resource.format.lower()
            original_size = len(image_resource.data)

            # Step 1: Resize if needed
            img_resized, new_width, new_height = self._resize_image(img)

            # Step 2: Determine output format
            output_format = self._determine_output_format(img_resized, original_format)

            # Step 3: Convert color mode if needed
            if output_format == 'jpeg':
                img_resized = self._convert_for_jpeg(img_resized)

            # Step 4: Save optimized image
            optimized_data = self._save_image(img_resized, output_format)

            # Step 5: Create new ImageResource
            new_filename = self._update_filename(image_resource.filename, output_format)

            new_size = len(optimized_data)
            if new_size < original_size:
                reduction = (1 - new_size / original_size) * 100
                logger.debug(f"Optimized {image_resource.filename}: {original_size} -> {new_size} bytes ({reduction:.1f}% reduction)")

            return ImageResource(
                id=image_resource.id,
                filename=new_filename,
                data=optimized_data,
                format=output_format if output_format != 'jpeg' else 'jpg',
                width=new_width,
                height=new_height,
                page_num=image_resource.page_num,
                bbox=image_resource.bbox
            )
        except Exception as e:
            logger.warning(f"Failed to optimize image {image_resource.filename}: {e}")
            # Return original on error
            return image_resource

    def _resize_image(self, img: Image.Image) -> Tuple[Image.Image, int, int]:
        """
        Resize image to fit within max dimensions.

        Preserves aspect ratio. Only downsizes, never upsizes.

        Returns:
            Tuple of (resized_image, new_width, new_height)
        """
        width, height = img.size
        max_w = self.config.max_width
        max_h = self.config.max_height

        # Check if resize is needed
        if width <= max_w and height <= max_h:
            return img, width, height

        # Calculate scaling factor
        scale_w = max_w / width
        scale_h = max_h / height
        scale = min(scale_w, scale_h)

        new_width = int(width * scale)
        new_height = int(height * scale)

        # Use high-quality resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")

        return resized, new_width, new_height

    def _determine_output_format(self, img: Image.Image, original_format: str) -> str:
        """
        Determine output format based on config and image properties.

        Args:
            img: PIL Image object
            original_format: Original file format

        Returns:
            Output format ('jpeg' or 'png' or 'gif')
        """
        # GIF stays as GIF (for animations)
        if original_format == 'gif':
            return 'gif'

        # PNG conversion logic
        if original_format == 'png':
            if self.config.convert_png_to_jpeg:
                # Check if image has meaningful transparency
                if self._has_transparency(img):
                    return 'png'  # Keep PNG for transparency
                return 'jpeg'
            return 'png'

        # JPEG stays as JPEG
        return 'jpeg'

    def _has_transparency(self, img: Image.Image) -> bool:
        """Check if image has meaningful transparency."""
        if img.mode not in ('RGBA', 'LA', 'PA'):
            return False

        if img.mode == 'RGBA':
            alpha = img.split()[3]
            # Check if any pixels are actually transparent
            extrema = alpha.getextrema()
            if extrema and isinstance(extrema, tuple) and len(extrema) == 2:
                min_alpha: int = extrema[0]  # type: ignore[assignment]
                return min_alpha < 255  # Min alpha < 255 means transparency
            return False

        return True  # Assume transparency for other modes

    def _convert_for_jpeg(self, img: Image.Image) -> Image.Image:
        """
        Convert image to RGB mode suitable for JPEG.

        Handles RGBA by compositing onto white background.
        """
        if img.mode == 'RGB':
            return img

        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, self.config.jpeg_background_color)
            # Composite the image onto white background
            background.paste(img, mask=img.split()[3])  # Use alpha as mask
            return background

        # Convert other modes (L, P, etc.) to RGB
        return img.convert('RGB')

    def _save_image(self, img: Image.Image, output_format: str) -> bytes:
        """
        Save image to bytes with appropriate settings.

        Args:
            img: PIL Image object
            output_format: Target format

        Returns:
            Image data as bytes
        """
        buffer = BytesIO()

        if output_format == 'jpeg':
            img.save(
                buffer,
                format='JPEG',
                quality=self.config.jpeg_quality,
                optimize=True
            )
        elif output_format == 'png':
            img.save(
                buffer,
                format='PNG',
                optimize=True
            )
        elif output_format == 'gif':
            img.save(buffer, format='GIF')
        else:
            # Fallback
            img.save(buffer, format=output_format.upper())

        return buffer.getvalue()

    def _update_filename(self, original_filename: str, new_format: str) -> str:
        """Update filename extension for new format."""
        if '.' in original_filename:
            base = original_filename.rsplit('.', 1)[0]
        else:
            base = original_filename

        ext = 'jpg' if new_format == 'jpeg' else new_format
        return f"{base}.{ext}"

    def optimize_batch(self, images: List[ImageResource]) -> List[ImageResource]:
        """
        Optimize a batch of images.

        Args:
            images: List of ImageResource objects

        Returns:
            List of optimized ImageResource objects
        """
        if not images:
            return images

        logger.info(f"Optimizing {len(images)} images...")
        optimized = [self.optimize(img) for img in images]

        # Calculate total savings
        original_total = sum(len(img.data) for img in images)
        optimized_total = sum(len(img.data) for img in optimized)

        if original_total > 0:
            savings = (1 - optimized_total / original_total) * 100
            logger.info(f"Image optimization complete: {original_total/1024:.1f}KB -> {optimized_total/1024:.1f}KB ({savings:.1f}% reduction)")

        return optimized
