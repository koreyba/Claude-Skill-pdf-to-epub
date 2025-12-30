from claude_skill.conversion.detectors.models import SemanticBlock, TextBlock
from claude_skill.conversion.detectors.footnote_detector import FootnoteDetector

def create_block(text: str, role: str = "body") -> SemanticBlock:
    tb = TextBlock(
        text=text, page=1, x0=0, y0=0, x1=100, y1=100,
        font_name="Arial", font_size=12, flags=0
    )
    return SemanticBlock(original_block=tb, role=role)

def test_detect_bracket_refs():
    detector = FootnoteDetector()
    blocks = [
        create_block("This is a statement [1]."),
        create_block("Another one [12] with text."),
        create_block("No reference here."),
    ]

    processed = detector.process(blocks)

    assert "footnote_refs" in processed[0].metadata
    refs_0 = processed[0].metadata["footnote_refs"]
    assert len(refs_0) == 1
    assert refs_0[0]["num"] == 1
    assert refs_0[0]["text"] == "[1]"

    assert "footnote_refs" in processed[1].metadata
    refs_1 = processed[1].metadata["footnote_refs"]
    assert len(refs_1) == 1
    assert refs_1[0]["num"] == 12
    assert refs_1[0]["text"] == "[12]"

    assert "footnote_refs" not in processed[2].metadata

def test_detect_parenthesis_refs():
    detector = FootnoteDetector()
    blocks = [
        create_block("Statement (1) and (2)."),
    ]

    processed = detector.process(blocks)
    refs = processed[0].metadata["footnote_refs"]
    assert len(refs) == 2
    assert refs[0]["num"] == 1
    assert refs[0]["text"] == "(1)"
    assert refs[1]["num"] == 2
    assert refs[1]["text"] == "(2)"

def test_ignore_headers():
    detector = FootnoteDetector()
    blocks = [
        create_block("Chapter 1 [1]", role="h1"), # Should ignore refs in headers usually? Or keep them?
    ]
    # Current logic ignores non-body
    processed = detector.process(blocks)
    assert "footnote_refs" not in processed[0].metadata
