"""Main conversion orchestrator."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
from dataclasses import asdict

from .strategies import SimpleStrategy
from .models import (
    ConversionConfig,
    ConversionResult,
    ConversionLog,
    BookMetadata,
    ExcludeRegions,
    PageRanges,
    MultiColumnConfig,
    HeadingConfig,
    FootnoteConfig,
    ImageOptimizationConfig,
    StructuredContent,
)
from core.epub_builder import EPUBBuilder


# Strategy registry
STRATEGY_REGISTRY = {
    "simple": SimpleStrategy,
    # Future: "academic": AcademicStrategy,
}


# Default configuration
DEFAULT_CONFIG = ConversionConfig(
    page_ranges=PageRanges(skip=[1, 2], content=(3, -3), endnotes=(-2, -1)),
    exclude_regions=ExcludeRegions(top=0.05, bottom=0.05, left=0.0, right=0.0),
    multi_column=MultiColumnConfig(enabled=False, column_count=1, threshold=0.4),
    reading_order_strategy="y_sort",
    heading_detection=HeadingConfig(font_size_threshold=1.2),
    footnote_processing=FootnoteConfig(enabled=False),
    metadata=BookMetadata(title=None, author=None, language="en"),  # None = extract from PDF
    image_optimization=ImageOptimizationConfig(enabled=True),  # Optimize images by default
)


class Converter:
    """
    Orchestrates PDF to EPUB conversion process.
    
    Coordinates the conversion workflow:
    1. Load and validate configuration
    2. Select appropriate strategy
    3. Execute conversion (extract → order → detect → build)
    4. Generate conversion log
    """
    
    def __init__(self, strategy: str = "simple"):
        """
        Initialize converter with strategy.
        
        Args:
            strategy: Conversion strategy name ("simple", "academic", etc.)
            
        Raises:
            ValueError: If strategy is unknown
        """
        if strategy not in STRATEGY_REGISTRY:
            available = list(STRATEGY_REGISTRY.keys())
            raise ValueError(f"Unknown strategy: {strategy}. Available: {available}")
        
        self.strategy_name = strategy
        self.strategy = STRATEGY_REGISTRY[strategy]()
        self.epub_builder = EPUBBuilder()
    
    def convert(
        self,
        pdf_path: Union[str, Path],
        output_path: Union[str, Path],
        config: Optional[ConversionConfig] = None,
        config_path: Optional[Path] = None
    ) -> ConversionResult:
        """
        Convert PDF to EPUB.
        
        Args:
            pdf_path: Path to input PDF file (str or Path)
            output_path: Path for output EPUB file (str or Path)
            config: Conversion configuration (or None for defaults)
            config_path: Path to JSON config file (alternative to config param)
            
        Returns:
            ConversionResult with status, EPUB path, and log
        """
        # Convert to Path objects
        pdf_path = Path(pdf_path)
        output_path = Path(output_path)
        # Initialize log
        log = ConversionLog(
            timestamp=datetime.now(),
            strategy_used=self.strategy_name,
            config={}
        )
        
        try:
            # Step 1: Load and validate configuration
            log.steps_completed.append("loading_config")
            if config is None:
                config = self._load_config(config_path)
            self._validate_config(config)
            log.config = asdict(config)
            
            # Step 2: Execute strategy conversion (extract → order → detect)
            log.steps_completed.append("extracting")
            structured_content = self.strategy.convert(pdf_path, config)
            
            # Check reading order confidence
            if structured_content.reading_order_confidence < 0.7:
                log.warnings.append(
                    f"Low reading order confidence: {structured_content.reading_order_confidence:.2f}. "
                    "Consider reviewing the output or adjusting configuration."
                )
            
            # Step 3: Build EPUB file
            log.steps_completed.append("building_epub")
            build_content = structured_content
            if hasattr(structured_content, "rendered_chapters"):
                build_content = StructuredContent(
                    chapters=structured_content.rendered_chapters,
                    metadata=structured_content.metadata,
                    reading_order_confidence=structured_content.reading_order_confidence,
                    images=structured_content.images
                )

            epub_path = self.epub_builder.build(build_content, output_path)
            
            # Determine status
            status = "success"
            if log.warnings:
                status = "warning"
            
            return ConversionResult(
                epub_path=epub_path,
                status=status,
                reading_order_confidence=structured_content.reading_order_confidence,
                log=log,
                structured_content=structured_content,
                metadata=structured_content.metadata
            )
        
        except FileNotFoundError as e:
            log.errors.append(f"{log.steps_completed[-1] if log.steps_completed else 'initialization'}: {str(e)}")
            return ConversionResult(
                epub_path=None,
                status="failed",
                reading_order_confidence=0.0,
                log=log
            )
        
        except Exception as e:
            step = log.steps_completed[-1] if log.steps_completed else "initialization"
            log.errors.append(f"{step}: {type(e).__name__}: {str(e)}")
            return ConversionResult(
                epub_path=None,
                status="failed",
                reading_order_confidence=0.0,
                log=log
            )
    
    def _load_config(self, config_path: Optional[Path]) -> ConversionConfig:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to JSON config file (or None for defaults)
            
        Returns:
            ConversionConfig instance
            
        Raises:
            ValueError: If config file is invalid JSON
        """
        if config_path is None:
            return DEFAULT_CONFIG
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Merge with defaults and deserialize nested dataclasses
        merged = self._deep_merge(asdict(DEFAULT_CONFIG), data)
        return ConversionConfig.from_dict(merged)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """
        Recursively merge override into base without losing nested defaults.
        """
        if not isinstance(override, dict):
            return override

        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value

        return merged
    
    def _validate_config(self, config: ConversionConfig) -> None:
        """
        Validate configuration (fail-fast approach).
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config is None:
            raise ValueError("Configuration cannot be None")
        
        # Validate exclude_regions (must be 0.0-1.0)
        for field in ['top', 'bottom', 'left', 'right']:
            value = getattr(config.exclude_regions, field)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"exclude_regions.{field} must be 0.0-1.0, got {value}")
        
        # Validate reading_order_strategy
        allowed_strategies = ["y_sort", "xy_cut", "column_based"]
        if config.reading_order_strategy not in allowed_strategies:
            raise ValueError(
                f"reading_order_strategy must be one of {allowed_strategies}, "
                f"got '{config.reading_order_strategy}'"
            )
        
        # Validate language code (basic check)
        if len(config.metadata.language) != 2:
            raise ValueError(
                f"metadata.language must be 2-letter ISO 639-1 code, "
                f"got '{config.metadata.language}'"
            )
