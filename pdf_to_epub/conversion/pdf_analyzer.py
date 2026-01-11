"""PDF structure analyzer - generates conversion config."""

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, List

import fitz

from .converter import DEFAULT_CONFIG
from .models import ConversionConfig, MultiColumnConfig
from core.utils import get_logger

logger = get_logger(__name__)


class PDFAnalyzer:
    """
    Analyzes PDF structure and generates a conversion config suggestion.

    This component:
    - Detects text layer presence
    - Analyzes font statistics
    - Detects multi-column layout
    - Produces a suggested ConversionConfig
    """

    def __init__(self, pdf_path: str):
        """
        Initialize analyzer with PDF file.

        Args:
            pdf_path: Path to PDF file to analyze
        """
        self.pdf_path = Path(pdf_path)
        self._analysis: Dict[str, Any] | None = None

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze PDF structure and generate an analysis report.

        Returns:
            dict: Analysis report with recommended hints
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        with fitz.open(str(self.pdf_path)) as doc:
            page_count = len(doc)
            metadata = doc.metadata or {}
            image_count = sum(len(page.get_images(full=True)) for page in doc)

            sample_pages = self._sample_pages(page_count, max_samples=5)
            x_cluster_counts: List[int] = []
            text_lengths: List[int] = []
            font_sizes: Counter = Counter()

            for page_index in sample_pages:
                page = doc.load_page(page_index)
                text = page.get_text().strip()
                text_lengths.append(len(text))

                blocks = page.get_text("dict")["blocks"]
                x_coords = [b["bbox"][0] for b in blocks if b.get("type") == 0]
                clusters = {round(x / 50) * 50 for x in x_coords}
                if clusters:
                    x_cluster_counts.append(len(clusters))

                for block in blocks:
                    if block.get("type") != 0:
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font_sizes[round(span.get("size", 0.0), 1)] += 1

            has_text_layer = any(length > 20 for length in text_lengths)
            multi_column, column_count = self._infer_columns(x_cluster_counts)
            body_font_size = font_sizes.most_common(1)[0][0] if font_sizes else None

            warnings = []
            if not has_text_layer:
                warnings.append("No text layer detected. PDF may be scanned.")

            analysis = {
                "pdf_path": str(self.pdf_path),
                "page_count": page_count,
                "image_count": image_count,
                "metadata": {
                    "title": metadata.get("title"),
                    "author": metadata.get("author"),
                    "language": metadata.get("language"),
                },
                "text_layer": {
                    "present": has_text_layer,
                    "sampled_pages": [p + 1 for p in sample_pages],
                },
                "layout": {
                    "multi_column_detected": multi_column,
                    "estimated_columns": column_count,
                    "x_cluster_counts": x_cluster_counts,
                },
                "fonts": {
                    "body_size": body_font_size,
                    "unique_sizes": len(font_sizes),
                },
                "warnings": warnings,
            }

            self._analysis = analysis
            return analysis

    def generate_config(self) -> Dict[str, Any]:
        """
        Generate conversion config based on analysis.

        Returns:
            dict: Conversion configuration as a dictionary
        """
        analysis = self._analysis or self.analyze()

        config = ConversionConfig.from_dict(asdict(DEFAULT_CONFIG))

        if analysis["layout"]["multi_column_detected"]:
            config.reading_order_strategy = "xy_cut"
            config.multi_column = MultiColumnConfig(
                enabled=True,
                column_count=analysis["layout"]["estimated_columns"],
                threshold=config.multi_column.threshold,
            )
        else:
            config.reading_order_strategy = "y_sort"
            config.multi_column = MultiColumnConfig(
                enabled=False,
                column_count=1,
                threshold=config.multi_column.threshold,
            )

        return asdict(config)

    def _sample_pages(self, page_count: int, max_samples: int) -> List[int]:
        if page_count <= max_samples:
            return list(range(page_count))

        indices = {0, page_count // 2, page_count - 1}
        while len(indices) < max_samples:
            indices.add(len(indices))
        return sorted(indices)

    def _infer_columns(self, x_cluster_counts: List[int]) -> tuple[bool, int]:
        if not x_cluster_counts:
            return False, 1

        median_clusters = sorted(x_cluster_counts)[len(x_cluster_counts) // 2]
        if median_clusters >= 2:
            return True, min(median_clusters, 3)
        return False, 1
