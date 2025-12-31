# ADAPTABLE: Can be extended or used as template for new strategies
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
"""Simple conversion strategy for single-column fiction books."""

from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF

from .base_strategy import BaseStrategy
from ..models import (
    StructuredContent,
    ImageResource,
    BookMetadata,
    Chapter,
    ImageOptimizationConfig,
)
from ...core.pdf_extractor import PDFExtractor
from ..detectors.models import TextBlock
from ..detectors.reading_order.y_sorter import YSorter
from ..detectors.reading_order.xy_cut_sorter import XYCutSorter
from ..detectors.font_analyzer import FontAnalyzer
from ..detectors.structure_classifier import StructureClassifier
from ..detectors.structure_builder import StructureBuilder


class SimpleStrategy(BaseStrategy):
    """
    Conversion strategy for simple single-column books (fiction, novels).
    
    Uses:
    - PDFExtractor for text extraction
    - Y-sort for reading order (top-to-bottom)
    - FontAnalyzer + StructureClassifier for chapter detection
    """
    
    def extract(self, pdf_path: Path, config) -> Tuple[List[TextBlock], List[ImageResource], BookMetadata]:
        """
        Extract text blocks, images, and metadata from PDF.
        
        Args:
            pdf_path: Path to the input PDF file
            config: Conversion configuration
            
        Returns:
            Tuple of (text_blocks, images, metadata)
        """
        # Step 1: Extract text blocks using PDFExtractor
        with PDFExtractor(pdf_path) as extractor:
            blocks = extractor.get_structural_blocks()

        # Step 2: Extract images from PDF
        images = self._extract_images(pdf_path)

        # Step 3: Optimize images if enabled
        if hasattr(config, 'image_optimization') and config.image_optimization.enabled:
            images = self._optimize_images(images, config.image_optimization)

        # Step 4: Extract metadata from PDF
        metadata = self._extract_metadata(pdf_path, config)

        return blocks, images, metadata
    
    def _extract_images(self, pdf_path: Path) -> List[ImageResource]:
        """
        Extract all images from PDF pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of ImageResource objects
        """
        images = []
        doc = fitz.open(str(pdf_path))
        
        try:
            for page_num, page in enumerate(doc, start=1):
                # Get all images on this page
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list, start=1):
                    try:
                        xref = img[0]  # Image reference number
                        base_image = doc.extract_image(xref)
                        
                        # Create ImageResource
                        image_resource = ImageResource(
                            id=f"img-page-{page_num}-{img_index}",
                            filename=f"image{len(images)+1:03d}.{base_image['ext']}",
                            data=base_image["image"],
                            format=base_image["ext"],
                            width=base_image["width"],
                            height=base_image["height"],
                            page_num=page_num
                        )
                        images.append(image_resource)
                    except Exception as e:
                        # Skip images that can't be extracted
                        print(f"Warning: Could not extract image {img_index} from page {page_num}: {e}")
                        continue
        finally:
            doc.close()
        
        return images

    def _optimize_images(
        self,
        images: List[ImageResource],
        config: ImageOptimizationConfig
    ) -> List[ImageResource]:
        """
        Optimize extracted images for EPUB.

        Args:
            images: List of ImageResource objects
            config: Image optimization configuration

        Returns:
            List of optimized ImageResource objects
        """
        from ...core.image_optimizer import (
            ImageOptimizer,
            ImageOptimizationConfig as OptConfig
        )

        opt_config = OptConfig(
            max_width=config.max_width,
            max_height=config.max_height,
            jpeg_quality=config.jpeg_quality,
            convert_png_to_jpeg=config.convert_png_to_jpeg
        )

        optimizer = ImageOptimizer(opt_config)
        return optimizer.optimize_batch(images)

    def _extract_metadata(self, pdf_path: Path, config) -> BookMetadata:
        """
        Extract metadata from PDF info dict.
        
        Falls back to config values or "Unknown" if metadata is not available.
        
        Args:
            pdf_path: Path to the PDF file
            config: Conversion configuration
            
        Returns:
            BookMetadata object
        """
        doc = fitz.open(str(pdf_path))
        
        try:
            pdf_meta = doc.metadata or {}
            
            # Extract metadata with fallback chain: config -> PDF info -> "Unknown"
            title = config.metadata.title if config.metadata.title else (pdf_meta.get('title') or "Unknown")
            author = config.metadata.author if config.metadata.author else (pdf_meta.get('author') or "Unknown")
            language = config.metadata.language or "en"
            publisher = pdf_meta.get('producer')
            description = pdf_meta.get('subject')
            
            metadata = BookMetadata(
                title=title,
                author=author,
                language=language,
                publisher=publisher,
                isbn=None,  # ISBN typically not in PDF metadata
                description=description
            )
        finally:
            doc.close()
        
        return metadata
    
    def order_blocks(self, blocks: List[TextBlock], config) -> Tuple[List[TextBlock], float]:
        """
        Order text blocks using simple Y-sort (top-to-bottom).
        
        Args:
            blocks: List of extracted text blocks
            config: Conversion configuration
            
        Returns:
            Tuple of (ordered blocks, confidence=1.0)
        """
        strategy = getattr(config, "reading_order_strategy", "y_sort")
        if strategy in ["xy_cut", "column_based"]:
            sorter = XYCutSorter()
        else:
            sorter = YSorter()
        ordered_blocks = sorter.sort_blocks(blocks)
        
        # Y-sort is deterministic, so confidence is always 1.0
        confidence = 1.0
        
        return ordered_blocks, confidence
    
    def detect_structure(
        self, 
        blocks: List[TextBlock], 
        config,
        images: List[ImageResource],
        metadata: BookMetadata
    ) -> StructuredContent:
        """
        Detect document structure from ordered blocks.
        
        Uses FontAnalyzer to identify heading fonts, then StructureClassifier
        to classify blocks, and StructureBuilder to group into chapters.
        
        Args:
            blocks: List of ordered text blocks
            config: Conversion configuration
            images: List of extracted images
            metadata: Book metadata
            
        Returns:
            StructuredContent with chapters, metadata, and images
        """
        # Step 1: Analyze fonts to identify heading fonts
        font_analyzer = FontAnalyzer()
        font_profile = font_analyzer.analyze(blocks)
        
        # Step 2: Classify each block as heading or paragraph
        classifier = StructureClassifier()
        classified_blocks = classifier.classify(blocks)
        
        # Step 3: Group into chapters
        builder = StructureBuilder()
        chapters = builder.build_chapters(classified_blocks)
        
        # Handle case where no chapters were detected
        if not chapters:
            # Create a single chapter with all content
            content_html = "\n".join(f"<p>{block.text}</p>" for block in blocks)
            chapters = [Chapter(
                title="Content",
                level=1,
                content=content_html,
                footnotes=[]
            )]
        
        # Create StructuredContent with extracted metadata and images
        structured = StructuredContent(
            chapters=chapters,
            metadata=metadata,
            reading_order_confidence=0.0,  # Will be set by BaseStrategy
            images=images
        )
        
        return structured
