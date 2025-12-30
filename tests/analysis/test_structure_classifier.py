import pytest
from claude_skill.detectors.models import TextBlock
from claude_skill.detectors.structure_classifier import StructureClassifier

def create_block(text, size=11.0, flags=0, y0=100, x0=50):
    return TextBlock(
        text=text,
        page=1,
        x0=x0, y0=y0, x1=x0+100, y1=y0+10,
        font_name="Arial",
        font_size=size,
        flags=flags
    )

@pytest.fixture
def classifier():
    return StructureClassifier()

def test_classify_standard_h1(classifier):
    # Case: Standard H1 (Large font)
    # Even without fancy heuristics, size difference should trigger H1 from FontAnalyzer or Score
    blocks = [
        create_block("Chapter 1", size=24.0, flags=16), # H1
        create_block("Usually body text is smaller.", size=12.0), # Body
    ]
    
    result = classifier.classify(blocks)
    assert result[0].role == "h1"
    assert result[1].role == "body"

def test_classify_heuristic_h1(classifier):
    # Case: "Holonic Conferencing" from user scan
    # Same size as body, but Bold + No Punct + Short + Spacing
    
    # Body Size = 11.0
    body_1 = create_block("Previous text ending here.", size=11.0, y0=100)
    
    # Header: Bold (flag 16), Short, No punct
    # Large top margin (y0=200, prev y1=110 -> gap 90). Body line height ~13. Gap > 1.5x.
    header = create_block("Holonic Conferencing", size=11.0, flags=16, y0=200)
    
    # Next body: Normal spacing
    body_2 = create_block("Subsequent text starting here.", size=11.0, y0=215)
    
    blocks = [body_1, header, body_2]
    
    result = classifier.classify(blocks)
    
    header_semantic = result[1]
    print(f"\nHeader Score: {header_semantic.score}")
    print(f"Signals: {header_semantic.debug_signals}")
    
    assert header_semantic.role == "h1" # Score should be >= 75
    assert "Bold" in header_semantic.debug_signals
    assert "NoPunct" in header_semantic.debug_signals
    assert "TopMargin" in header_semantic.debug_signals

def test_classify_simple_bold_in_text(classifier):
    # Case: Bold text that is NOT a header (e.g. valid bold term in paragraph)
    # It has valid punctuation or is part of flow (small margins)
    
    body_1 = create_block("This concept is called", size=11.0, y0=100)
    # Bold term, but close to previous line
    bold_term = create_block("Important Term.", size=11.0, flags=16, y0=112) 
    body_2 = create_block("which means...", size=11.0, y0=124)
    
    blocks = [body_1, bold_term, body_2]
    
    result = classifier.classify(blocks)
    
    term = result[1]
    # Should NOT be H1/H2 because margins are small and it has punctuation (maybe)
    # Score should be < 50
    assert term.role == "body" 
    # It might get score for Bold (+30), but lose on spacing and punct if present.
    # Actually "Important Term." has punct, so no +20. 
    # Margins small, so no +10/+15.
    # Total score ~30-40.
    assert term.score < 50

def test_list_item_detection(classifier):
    blocks = [
        create_block("• Item one"),
        create_block("1. Item two"),
        create_block("Regular paragraph")
    ]
    result = classifier.classify(blocks)
    assert result[0].role == "list-item"
    assert result[1].role == "list-item"
    assert result[2].role == "body"
