# ADAPTABLE: Can be extended with new hook methods
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
"""Base class for conversion strategies."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Union

# Import types that will be defined in models.py
# For now, we'll use forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conversion.models import ConversionConfig, StructuredContent, ImageResource, BookMetadata
    from conversion.detectors.models import TextBlock


class BaseStrategy(ABC):
    """
    Abstract base class for conversion strategies.
    
    Defines the interface and template method for all conversion strategies.
    Subclasses must implement extract(), order_blocks(), and detect_structure().
    
    The convert() method implements the Template Method pattern, calling hooks
    in a specific order: extract → order_blocks → detect_structure.
    """
    
    def convert(self, pdf_path: Union[str, Path], config: 'ConversionConfig') -> 'StructuredContent':
        """
        Template method that orchestrates the conversion workflow.
        
        This method defines the overall algorithm and calls hook methods
        that subclasses override to customize behavior.
        
        Workflow:
        1. Extract text blocks, images, and metadata from PDF
        2. Order blocks into reading order
        3. Detect document structure (chapters, headings)
        
        Args:
            pdf_path: Path to the input PDF file (str or Path)
            config: Conversion configuration
            
        Returns:
            StructuredContent: Structured representation of the document
            
        Raises:
            ValueError: If config is invalid
            FileNotFoundError: If PDF does not exist
        """
        # Convert to Path and validate
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self._validate_config(config)
        
        # Step 1: Extract text blocks, images, and metadata
        blocks, images, metadata = self.extract(pdf_path, config)
        
        # Step 2: Order blocks into reading order
        ordered_blocks, confidence = self.order_blocks(blocks, config)
        
        # Step 3: Detect structure (chapters, headings, etc.)
        structured_content = self.detect_structure(ordered_blocks, config, images, metadata)
        
        # Add reading order confidence to result
        structured_content.reading_order_confidence = confidence
        
        return structured_content
    
    @abstractmethod
    def extract(self, pdf_path: Path, config: 'ConversionConfig') -> Tuple[List['TextBlock'], List['ImageResource'], 'BookMetadata']:
        """
        Extract text blocks, images, and metadata from PDF.
        
        Hook method for customizing text extraction.
        Subclasses can override to add custom extraction logic.
        
        Args:
            pdf_path: Path to the input PDF file
            config: Conversion configuration
            
        Returns:
            Tuple of (text_blocks, images, metadata)
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement extract()")
    
    @abstractmethod
    def order_blocks(
        self, 
        blocks: List['TextBlock'], 
        config: 'ConversionConfig'
    ) -> Tuple[List['TextBlock'], float]:
        """
        Order text blocks into reading order.
        
        Hook method for customizing reading order detection.
        Different strategies may use different algorithms (Y-sort, XY-cut, etc.).
        
        Args:
            blocks: List of extracted text blocks
            config: Conversion configuration
            
        Returns:
            Tuple of (ordered blocks, confidence score 0.0-1.0)
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement order_blocks()")
    
    @abstractmethod
    def detect_structure(
        self, 
        blocks: List['TextBlock'], 
        config: 'ConversionConfig',
        images: List['ImageResource'],
        metadata: 'BookMetadata'
    ) -> 'StructuredContent':
        """
        Detect document structure from ordered blocks.
        
        Hook method for customizing structure detection.
        Identifies chapters, headings, footnotes, and builds hierarchical structure.
        
        Args:
            blocks: List of ordered text blocks
            config: Conversion configuration
            images: List of extracted images
            metadata: Extracted book metadata
            
        Returns:
            StructuredContent with chapters, metadata, images
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement detect_structure()")
    
    def _validate_config(self, config: 'ConversionConfig') -> None:
        """
        Validate conversion configuration.
        
        Basic validation is performed here. Subclasses can override
        to add strategy-specific validation.
        
        Args:
            config: Conversion configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config is None:
            raise ValueError("Configuration cannot be None")
        
        # Additional validation can be added by subclasses
