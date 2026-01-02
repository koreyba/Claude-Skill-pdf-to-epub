"""Conversion module - PDF to EPUB conversion logic."""

from .models import (
    BookMetadata,
    ImageResource,
    Footnote,
    Chapter,
    StructuredContent,
    ConversionLog,
    ConversionResult,
)
from .strategies import BaseStrategy

__all__ = [
    'BookMetadata',
    'ImageResource',
    'Footnote',
    'Chapter',
    'StructuredContent',
    'ConversionLog',
    'ConversionResult',
    'BaseStrategy',
]
