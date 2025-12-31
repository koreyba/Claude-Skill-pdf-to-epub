from pathlib import Path

import pytest

from claude_skill.conversion.pdf_analyzer import PDFAnalyzer
from claude_skill.validation.validator import Validator


@pytest.fixture
def pdf_path():
    return Path(__file__).parent.parent / "fixtures" / "Excerpt C The Ways We Are in This Together.pdf"


@pytest.fixture
def epub_path():
    return Path(__file__).parent.parent / "fixtures" / "Excerpt C The Ways We Are in This Together.epub"


def test_pdf_analyzer_report_and_config(pdf_path):
    assert pdf_path.exists(), f"PDF fixture not found: {pdf_path}"

    analyzer = PDFAnalyzer(pdf_path)
    analysis = analyzer.analyze()
    config = analyzer.generate_config()

    assert analysis["page_count"] > 0
    assert analysis["text_layer"]["present"] is True
    assert "layout" in analysis

    assert config["reading_order_strategy"] in ("y_sort", "xy_cut")
    if analysis["layout"]["multi_column_detected"]:
        assert config["reading_order_strategy"] == "xy_cut"
        assert config["multi_column"]["enabled"] is True
    else:
        assert config["reading_order_strategy"] == "y_sort"
        assert config["multi_column"]["enabled"] is False


def test_validator_report_passes(pdf_path, epub_path):
    assert pdf_path.exists(), f"PDF fixture not found: {pdf_path}"
    assert epub_path.exists(), f"EPUB fixture not found: {epub_path}"

    validator = Validator(pdf_path, epub_path)
    report = validator.validate()

    assert report["status"] == "pass"
    completeness = report["details"]["completeness"]
    order = report["details"]["order"]

    assert completeness["score"] >= Validator.COMPLETENESS_THRESHOLD
    assert order["score"] >= Validator.ORDER_THRESHOLD
