from pathlib import Path

import pytest

from claude_skill.conversion.converter import Converter
from claude_skill.conversion.pdf_analyzer import PDFAnalyzer
from claude_skill.validation.validator import Validator


@pytest.fixture
def pdf_path():
    return Path(__file__).parent.parent / "fixtures" / "Excerpt_B_The_Many_Ways_We_Touch_Three_P.pdf"


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"


@pytest.fixture
def epub_path(pdf_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "excerpt_b.epub"

    converter = Converter(strategy="simple")
    result = converter.convert(str(pdf_path), str(output_path))

    assert result.status in ("success", "warning")
    return Path(result.epub_path)


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
