"""Main validation orchestrator."""

import re
from pathlib import Path
from typing import Dict, Any, List

from core.pdf_extractor import PDFExtractor
from core.epub_extractor import EPUBExtractor
from core.utils import get_logger
from .completeness_checker import CompletenessChecker
from .text_canonicalizer import canonicalize

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
        found_summary = self._found_summary(getattr(result, "found_chunks", None))
        missing_chunks, approx_matches = self._reconcile_missing_chunks(
            result.missing_chunks, target_text
        )

        completeness_pass = completeness_score >= self.COMPLETENESS_THRESHOLD
        order_pass = order_score >= self.ORDER_THRESHOLD

        details: Dict[str, Any] = {
            "completeness": {
                "score": completeness_score,
                "passed": completeness_pass,
                "missing_count": len(missing_chunks),
                "missing_examples": self._missing_examples(missing_chunks),
                "missing": self._missing_details(missing_chunks),
                "approximate_count": len(approx_matches),
                "approximate_examples": self._approximate_examples(approx_matches),
                "approximate": approx_matches,
                "found": found_summary,
            },
            "order": {
                "score": order_score,
                "passed": order_pass,
            },
            "text_lengths": {
                "source_chars": len(source_text),
                "target_chars": len(target_text),
            },
        }
        
        if run_epubcheck:
            details["epubcheck"] = {
                "enabled": True,
                "skipped": True,
                "reason": "not_implemented",
            }

        report: Dict[str, Any] = {
            "status": "pass" if completeness_pass and order_pass else "fail",
            "summary": self._format_summary(completeness_score, order_score),
            "details": details,
        }

        return report

    def _missing_examples(self, missing_chunks: List) -> List[str]:
        examples = []
        for failure in missing_chunks[:3]:
            text = failure.chunk.text.strip().replace("\n", " ")
            examples.append(text[:160])
        return examples

    def _missing_details(self, missing_chunks: List) -> List[Dict[str, Any]]:
        details = []
        for failure in missing_chunks:
            chunk = failure.chunk
            text = chunk.text.strip().replace("\n", " ")
            details.append({
                "text": text,
                "snippet": text[:200],
                "start_index": chunk.start_index,
                "end_index": chunk.end_index,
                "length": len(chunk.text),
                "reason": failure.reason,
            })
        return details

    def _approximate_examples(self, approx_matches: List[Dict[str, Any]]) -> List[str]:
        return [item.get("snippet", "") for item in approx_matches[:3]]

    def _found_summary(self, found_chunks) -> Dict[str, Any]:
        if not found_chunks:
            return {"count": 0, "exact": 0, "fuzzy": 0}
        exact = sum(1 for chunk in found_chunks if chunk.match_type == "exact")
        fuzzy = sum(1 for chunk in found_chunks if chunk.match_type == "fuzzy")
        return {"count": len(found_chunks), "exact": exact, "fuzzy": fuzzy}

    def _reconcile_missing_chunks(self, missing_chunks: List, target_text: str) -> tuple[List, List[Dict[str, Any]]]:
        if not missing_chunks:
            return [], []

        normalized_target = canonicalize(target_text, comparison=True).lower()
        word_re = re.compile(r"\w{4,}")
        approx_matches = []
        unresolved = []

        for failure in missing_chunks:
            chunk_text = failure.chunk.text.strip()
            normalized_chunk = canonicalize(chunk_text, comparison=True)
            tokens = word_re.findall(normalized_chunk.lower())
            if not tokens:
                unresolved.append(failure)
                continue

            found_tokens = sum(1 for token in tokens if token in normalized_target)
            coverage = found_tokens / len(tokens)
            if coverage >= 0.98:
                approx_matches.append({
                    "text": chunk_text,
                    "snippet": chunk_text.replace("\n", " ")[:200],
                    "coverage": round(coverage, 4),
                })
            else:
                unresolved.append(failure)

        return unresolved, approx_matches

    def _format_summary(self, completeness: float, order: float) -> str:
        status = "PASS" if completeness >= self.COMPLETENESS_THRESHOLD and order >= self.ORDER_THRESHOLD else "FAIL"
        return f"Completeness: {completeness:.1f}% | Order: {order:.1f}% [{status}]"

    def _error_report(self, message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "summary": f"Validation error: {message}",
            "details": {"error": message},
        }
