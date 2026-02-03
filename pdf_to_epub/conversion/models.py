"""Data models for PDF to EPUB conversion."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class PageRanges:
    """Page ranges configuration."""
    skip: List[int] = field(default_factory=list)
    content: Tuple[int, int] = (1, -1)
    endnotes: Tuple[int, int] = (-1, -1)


@dataclass
class ExcludeRegions:
    """Exclude regions configuration (as percentages 0.0-1.0)."""
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0


@dataclass
class MultiColumnConfig:
    """Multi-column detection configuration."""
    enabled: bool = False
    column_count: int = 1
    threshold: float = 0.4


@dataclass
class HeadingConfig:
    """Heading detection configuration."""
    font_size_threshold: float = 1.2


@dataclass
class FootnoteConfig:
    """Footnote processing configuration."""
    enabled: bool = False
    patterns: List[str] = field(default_factory=lambda: ['bracket', 'paren', 'spaced', 'spaced_closer', 'keyword'])
    generate_backlinks: bool = True


@dataclass
class ImageOptimizationConfig:
    """Image optimization configuration."""
    enabled: bool = True
    max_width: int = 1200
    max_height: int = 1600
    jpeg_quality: int = 85
    convert_png_to_jpeg: bool = False


@dataclass
class BookMetadata:
    """
    Metadata for a book.
    
    Attributes:
        title: Book title
        author: Book author
        language: ISO 639-1 language code (e.g., "en", "ru")
        publisher: Publisher name (optional)
        isbn: ISBN identifier (optional)
        description: Book description (optional)
    """
    title: Optional[str]
    author: Optional[str]
    language: str
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate metadata fields."""
        # Allow None (will be filled from PDF), but validate non-empty strings
        if self.title is not None and not self.title.strip():
            raise ValueError("Title cannot be empty string")
        if self.author is not None and not self.author.strip():
            raise ValueError("Author cannot be empty string")
        if len(self.language) != 2:
            raise ValueError(f"Language must be 2-letter ISO 639-1 code, got '{self.language}'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookMetadata':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ImageResource:
    """
    Represents an image extracted from PDF.
    
    Attributes:
        id: Unique identifier (e.g., "img-page-5-1")
        filename: Filename for EPUB (e.g., "image001.png")
        data: Binary image data
        format: Image format ("png", "jpeg", "gif")
        width: Image width in pixels
        height: Image height in pixels
        page_num: Source page number in PDF
    """
    id: str
    filename: str
    data: bytes
    format: str
    width: int
    height: int
    page_num: int
    bbox: Optional[Tuple[float, float, float, float]] = None
    
    def __post_init__(self):
        """Validate image resource fields."""
        if self.format not in ['png', 'jpeg', 'jpg', 'gif']:
            raise ValueError(f"Unsupported image format: {self.format}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Image dimensions must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding binary data)."""
        d = asdict(self)
        # Don't include binary data in dict representation
        d['data'] = f"<{len(self.data)} bytes>"
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageResource':
        """Create from dictionary."""
        # Note: binary data should be provided separately
        return cls(**data)


@dataclass
class Footnote:
    """
    Represents a footnote or endnote.
    
    Attributes:
        marker: Footnote marker (e.g., "[1]", "1")
        id: Unique identifier for linking (e.g., "fn-chapter-1-note-1")
        text: Footnote text content
    """
    marker: str
    id: str
    text: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Footnote':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Chapter:
    """
    Represents a chapter in the structured content.
    
    Attributes:
        title: Chapter title
        level: Heading level (1-3 for H1/H2/H3)
        content: HTML content of the chapter
        footnotes: List of footnotes in this chapter
    """
    title: str
    level: int
    content: str
    footnotes: List[Footnote] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate chapter fields."""
        if self.level not in [1, 2, 3]:
            raise ValueError(f"Chapter level must be 1-3, got {self.level}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chapter':
        """Create from dictionary."""
        # Convert footnotes from dicts
        if 'footnotes' in data:
            data['footnotes'] = [Footnote.from_dict(f) for f in data['footnotes']]
        return cls(**data)


@dataclass
class StructuredContent:
    """
    Structured representation of a document.
    
    Attributes:
        chapters: List of chapters
        metadata: Book metadata
        reading_order_confidence: Confidence score for reading order (0.0-1.0)
        images: List of extracted images
    """
    chapters: List[Chapter]
    metadata: BookMetadata
    reading_order_confidence: float
    images: List[ImageResource] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate structured content."""
        if not 0.0 <= self.reading_order_confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.reading_order_confidence}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructuredContent':
        """Create from dictionary."""
        # Convert nested objects
        data['chapters'] = [Chapter.from_dict(c) for c in data['chapters']]
        data['metadata'] = BookMetadata.from_dict(data['metadata'])
        if 'images' in data:
            data['images'] = [ImageResource.from_dict(i) for i in data['images']]
        return cls(**data)


@dataclass
class ConversionLog:
    """
    Log of conversion process.
    
    Attributes:
        timestamp: When conversion started
        strategy_used: Name of strategy used
        config: Configuration used (as dict)
        steps_completed: List of completed step names
        warnings: List of warning messages
        errors: List of error messages
    """
    timestamp: datetime
    strategy_used: str
    config: Dict[str, Any]
    steps_completed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        # Convert datetime to ISO format
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionLog':
        """Create from dictionary."""
        # Convert timestamp from string
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ConversionResult:
    """
    Result of PDF to EPUB conversion.
    
    Attributes:
        epub_path: Path to generated EPUB file (None if failed)
        status: Conversion status ("success", "warning", "failed")
        reading_order_confidence: Confidence score for reading order
        log: Conversion log
        structured_content: Structured content (for analysis)
        metadata: Extracted metadata (for analysis)
    """
    epub_path: Optional[Path]
    status: str
    reading_order_confidence: float
    log: ConversionLog
    structured_content: Optional['StructuredContent'] = None
    metadata: Optional[BookMetadata] = None
    
    def __post_init__(self):
        """Validate conversion result."""
        if self.status not in ['success', 'warning', 'failed']:
            raise ValueError(f"Invalid status: {self.status}")
        if not 0.0 <= self.reading_order_confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.reading_order_confidence}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        # Convert Path to string
        if self.epub_path:
            d['epub_path'] = str(self.epub_path)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionResult':
        """Create from dictionary."""
        # Convert path from string
        if data.get('epub_path'):
            data['epub_path'] = Path(data['epub_path'])
        # Convert log
        data['log'] = ConversionLog.from_dict(data['log'])
        return cls(**data)


@dataclass
class ConversionConfig:
    """
    Configuration for PDF to EPUB conversion.

    Attributes:
        page_ranges: Page range configuration
        exclude_regions: Region exclusion configuration
        multi_column: Multi-column detection configuration
        reading_order_strategy: Reading order algorithm ("y_sort", "xy_cut", "column_based")
        heading_detection: Heading detection configuration
        footnote_processing: Footnote processing configuration
        metadata: Book metadata
        image_optimization: Image optimization configuration
    """
    page_ranges: PageRanges
    exclude_regions: ExcludeRegions
    multi_column: MultiColumnConfig
    reading_order_strategy: str
    heading_detection: HeadingConfig
    footnote_processing: FootnoteConfig
    metadata: BookMetadata
    image_optimization: ImageOptimizationConfig = field(default_factory=ImageOptimizationConfig)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.reading_order_strategy not in ['y_sort', 'xy_cut', 'column_based']:
            raise ValueError(f"Invalid reading_order_strategy: {self.reading_order_strategy}")
        # Validate exclude_regions are 0.0-1.0
        for field_name in ['top', 'bottom', 'left', 'right']:
            val = getattr(self.exclude_regions, field_name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"exclude_regions.{field_name} must be 0.0-1.0, got {val}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionConfig':
        """Create from dictionary."""
        # Convert nested dataclasses
        data['page_ranges'] = PageRanges(**data['page_ranges'])
        data['exclude_regions'] = ExcludeRegions(**data['exclude_regions'])
        data['multi_column'] = MultiColumnConfig(**data['multi_column'])
        data['heading_detection'] = HeadingConfig(**data['heading_detection'])
        data['footnote_processing'] = FootnoteConfig(**data['footnote_processing'])
        data['metadata'] = BookMetadata.from_dict(data['metadata'])
        if 'image_optimization' in data:
            data['image_optimization'] = ImageOptimizationConfig(**data['image_optimization'])
        return cls(**data)


# Re-export all models
__all__ = [
    'PageRanges',
    'ExcludeRegions',
    'MultiColumnConfig',
    'HeadingConfig',
    'FootnoteConfig',
    'ImageOptimizationConfig',
    'BookMetadata',
    'ImageResource',
    'Footnote',
    'Chapter',
    'StructuredContent',
    'ConversionLog',
    'ConversionResult',
    'ConversionConfig',
]
