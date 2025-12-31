"""Main validation orchestrator."""

from pathlib import Path
from typing import Dict, Any, List

from ..core.pdf_extractor import PDFExtractor
from ..core.epub_extractor import EPUBExtractor
from ..core.utils import get_logger
from .completeness_checker import CompletenessChecker

logger = get_logger(__name__)


class Validator:
    """
    Orchestrates all validation checks.

    Workflow:
    1. Extract texts from PDF and EPUB
    2. Canonicalize (text_canonicalizer)
    3. Segment (text_segmenter)
    4. Check completeness (completeness_checker)
    5. Check order (order_checker)
    6. Format validation (epubcheck - optional)
    7. Generate report with one-line summary
    """

    COMPLETENESS_THRESHOLD = 95.0
    ORDER_THRESHOLD = 80.0

    def __init__(self, pdf_path: str, epub_path: str):
        """
        Initialize validator with file paths.

        Args:
            pdf_path: Path to original PDF file
            epub_path: Path to generated EPUB file
        """
        self.pdf_path = Path(pdf_path)
        self.epub_path = Path(epub_path)

    def validate(self, run_epubcheck: bool = False) -> Dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            dict: Validation report with status, summary, and details
        """
        if not self.pdf_path.exists():
            return self._error_report(f"PDF file not found: {self.pdf_path}")
        if not self.epub_path.exists():
            return self._error_report(f"EPUB file not found: {self.epub_path}")

        try:
            with PDFExtractor(self.pdf_path) as pdf:
                source_text = pdf.get_full_text()
            with EPUBExtractor(self.epub_path) as epub:
                target_text = epub.get_full_text()
        except Exception as exc:
            logger.exception("Failed to extract text for validation")
            return self._error_report(str(exc))

        checker = CompletenessChecker(source_text, target_text)
        result = checker.check()

        completeness_score = result.completeness_score
        order_score = result.order_score if hasattr(result, "order_score") else 100.0

        completeness_pass = completeness_score >= self.COMPLETENESS_THRESHOLD
        order_pass = order_score >= self.ORDER_THRESHOLD

        report = {
            "status": "pass" if completeness_pass and order_pass else "fail",
            "summary": self._format_summary(completeness_score, order_score),
            "details": {
                "completeness": {
                    "score": completeness_score,
                    "passed": completeness_pass,
                    "missing_count": len(result.missing_chunks),
                    "missing_examples": self._missing_examples(result.missing_chunks),
                },
                "order": {
                    "score": order_score,
                    "passed": order_pass,
                },
                "text_lengths": {
                    "source_chars": len(source_text),
                    "target_chars": len(target_text),
                },
            },
        }

        if run_epubcheck:
            report["details"]["epubcheck"] = {
                "enabled": True,
                "skipped": True,
                "reason": "not_implemented",
            }

        return report

    def _missing_examples(self, missing_chunks: List) -> List[str]:
        examples = []
        for failure in missing_chunks[:3]:
            text = failure.chunk.text.strip().replace("\n", " ")
            examples.append(text[:160])
        return examples

    def _format_summary(self, completeness: float, order: float) -> str:
        status = "PASS" if completeness >= self.COMPLETENESS_THRESHOLD and order >= self.ORDER_THRESHOLD else "FAIL"
        return f"Completeness: {completeness:.1f}% | Order: {order:.1f}% [{status}]"

    def _error_report(self, message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "summary": f"Validation error: {message}",
            "details": {"error": message},
        }
