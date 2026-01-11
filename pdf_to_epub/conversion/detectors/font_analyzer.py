from typing import List, Dict, Tuple
from collections import defaultdict
from .models import TextBlock
from core.utils import get_logger

logger = get_logger(__name__)

class FontAnalyzer:
    """
    Analyzes font statistics to identify body text style and potential headings.
    """
    
    def analyze(self, blocks: List[TextBlock]) -> Dict[Tuple[str, float, int], str]:
        """
        Returns a mapping of font keys to roles.
        Example: {('Arial', 12.0, 0): 'body', ('Arial', 24.0, 1): 'h1'}
        """
        if not blocks:
            return {}
            
        # 1. Collect statistics (Area coverage is better than character count, 
        # but character count is easier if blocks have clean text)
        stats: Dict[Tuple[str, float, int], int] = defaultdict(int) # (name, size, flags) -> total_len
        
        for b in blocks:
            key = (b.font_name, round(b.font_size, 1), b.flags)
            stats[key] += len(b.text.strip())
            
        if not stats:
            return {}
            
        # 2. Identify Body Text (Most frequent style by content length)
        body_style = max(stats.items(), key=lambda x: x[1])[0]
        logger.info(f"Detected Body Style: {body_style} (coverage: {stats[body_style]} chars)")
        
        body_size = body_style[1]
        
        # 3. Classify others relative to body
        style_map = {}
        style_map[body_style] = "body"
        
        # Store styles sorted by size descending to assign H1, H2...
        potential_headers = []
        
        for style, count in stats.items():
            if style == body_style:
                continue
                
            name, size, flags = style
            
            # Heuristics
            if size > body_size * 1.2: # Significantly larger
                potential_headers.append(style)
            elif size < body_size * 0.9: # Smaller
                style_map[style] = "footnote_or_small"
            elif (flags & 2 ** 4): # Is Bold (fitz flag 2^4 = 16 usually, but need to check mappings)
                # Same size but bold -> likely strong emphasis or run-in head
                style_map[style] = "strong"
            else:
                style_map[style] = "body_variant" # e.g. italic body
                
        # Assign Header levels
        # Sort headers by size descending
        potential_headers.sort(key=lambda s: s[1], reverse=True)
        
        for i, style in enumerate(potential_headers):
            level = min(i + 1, 6) # H1..H6
            style_map[style] = f"h{level}"
            
        return style_map
