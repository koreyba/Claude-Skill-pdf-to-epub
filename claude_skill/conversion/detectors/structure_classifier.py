# ADAPTABLE: Heading detection heuristics can be tuned
# See ~/.claude/skills/pdf-to-epub/reference/code-adaptation.md
import re
from typing import List, Dict
from claude_skill.conversion.detectors.models import TextBlock, SemanticBlock
from claude_skill.conversion.detectors.font_analyzer import FontAnalyzer

# Pattern for endnotes: digit(s) followed by 2+ spaces at start
ENDNOTE_PATTERN = re.compile(r'^(\d{1,2})\s{2,}')

class StructureClassifier:
    """
    Classifies raw TextBlocks into SemanticBlocks (H1, Body, Footnote, etc.)
    using font statistics.
    """
    
    def __init__(self):
        self.font_analyzer = FontAnalyzer()
        
    def classify(self, blocks: List[TextBlock], config_overrides: Dict = None) -> List[SemanticBlock]:
        """
        Enrich blocks with semantic roles.
        """
        if not blocks:
            return []
            
        # 1. Analyze fonts to build style map
        style_map = self.font_analyzer.analyze(blocks)
        
        # Apply overrides if any (e.g. force specific font to be H1)
        # TODO: Implement config overrides
        
        semantic_blocks = []
        body_key = None
        for key, role in style_map.items():
            if role == "body":
                body_key = key
                break
                
        # Retrieve body properties for comparison
        # key structure: (name, size, flags)
        body_size = body_key[1] if body_key else 11.0 # Default fallback
        body_flags = body_key[2] if body_key else 0
        
        for i, block in enumerate(blocks):
            prev_block = blocks[i-1] if i > 0 else None
            next_block = blocks[i+1] if i < len(blocks) - 1 else None
            
            score, signals = self._calculate_heading_score(block, prev_block, next_block, body_size, body_flags)
            
            # Determine role based on score
            role = "body"
            if score >= 75:
                role = "h1"
            elif score >= 50:
                role = "h2"
            
            # Explicit override from FontAnalyzer (if it detected HUGE font)
            # We respect strong font signals if they align with our heuristics
            font_role = style_map.get((block.font_name, round(block.font_size, 1), block.flags), "body")
            if font_role.startswith("h") and int(font_role[1:]) <= 2:
                 # If FontAnalyzer was SUPER sure (very large size), trust it regardless of punctuation score
                 if role == "body": 
                     role = font_role

            # List item check (post-processing)
            if role == "body" and self._is_list_item(block.text.strip()):
                 role = "list-item"

            # Endnote check - format: "1  More technically..." with smaller font
            endnote_num = self._is_endnote(block, body_size)
            if endnote_num is not None and role == "body":
                role = "endnote"

            sb = SemanticBlock(
                original_block=block,
                role=role,
                score=score,
                debug_signals=signals,
                endnote_num=endnote_num  # Store parsed endnote number
            )
            semantic_blocks.append(sb)
            
        return semantic_blocks

    def _calculate_heading_score(self, block: TextBlock, prev: TextBlock, next_b: TextBlock, body_size: float, body_flags: int) -> tuple[float, list]:
        score = 0.0
        signals = []
        text = block.text.strip()
        
        if not text:
            return 0.0, []

        is_same_page_prev = prev and prev.page == block.page
        is_same_page_next = next_b and next_b.page == block.page

        # 1. Style Distinction (Bold)
        # Check fitz flags for bold (usually bit 4 -> 16)
        is_bold = (block.flags & 16) != 0
        body_is_bold = (body_flags & 16) != 0
        
        if is_bold and not body_is_bold:
            score += 30
            signals.append("Bold")
            
        # 2. Size Distinction
        size_diff = block.font_size - body_size
        if size_diff > 0.5:
            points = size_diff * 10
            score += points
            signals.append(f"Size+{size_diff:.1f}")
            
        # 3. Format: No terminal punctuation
        if text[-1] not in ".:;?!,": 
            score += 20
            signals.append("NoPunct")
            
        # 4. Format: Length (Short implies heading)
        if len(text) < 150:
            score += 10
            signals.append("Short")
        if len(text) < 50: # Very short
             score += 5
             
        # 5. Format: Uppercase
        if text.isupper() and len(text) > 4:
            score += 10
            signals.append("ALLCAPS")
            
        # 6. Spacing: Top vs Bottom
        # Only relevant if blocks are on the same page
        top_margin = 0
        bottom_margin = 0
        
        if is_same_page_prev:
            top_margin = block.y0 - prev.y1
            
        if is_same_page_next:
            bottom_margin = next_b.y0 - block.y1
            
        # Significant Top Gap? (e.g. > 1.5x bottom gap, or just absolute large gap)
        # We assume standard line height is approx body_size * 1.2
        line_height = body_size * 1.2
        
        if top_margin > line_height * 1.5:
             score += 10
             signals.append("TopMargin")
             
        if top_margin > bottom_margin * 1.5 and bottom_margin > 0:
             score += 15
             signals.append("Top>Bottom")

        return score, signals

    def _is_list_item(self, text: str) -> bool:
        # Simple heuristic
        if text.startswith("•") or text.startswith("- "):
            return True
        # Check "1. ", "2. ", "10. ", etc.
        if re.match(r'^\d+\.\s', text):
            return True
        return False

    def _is_endnote(self, block: TextBlock, body_size: float) -> int | None:
        """
        Check if block is an endnote. Endnotes typically:
        1. Start with a number followed by 2+ spaces
        2. Have font size smaller than or equal to body text

        Format: "1  More technically, theories and paradigms tetra-enact..."

        Args:
            block: The TextBlock to check
            body_size: The body font size for comparison

        Returns the endnote number if detected, None otherwise.
        """
        text = block.text.strip()
        match = ENDNOTE_PATTERN.match(text)
        if match:
            num = int(match.group(1))
            # Reasonable endnote numbers (1-99)
            if 1 <= num <= 99:
                # Endnotes typically have same or smaller font than body
                # Allow small tolerance (endnotes shouldn't be much larger than body)
                if block.font_size <= body_size + 0.5:
                    return num
        return None
