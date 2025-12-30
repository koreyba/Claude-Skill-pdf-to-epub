from typing import List, Tuple
import re
from claude_skill.conversion.detectors.models import SemanticBlock

class FootnoteDetector:
    """
    Detects footnote references in text blocks.
    Currently uses Regex patterns. Future improvement: use span position detectors.
    """
    
    # Matches [1], [12], (1), (12)
    REF_PATTERN = re.compile(r'(\[\d+\]|\(\d+\))')
    
    def process(self, blocks: List[SemanticBlock]) -> List[SemanticBlock]:
        """
        Scans blocks for footnote references and tags them.
        (Note: Ideally we should insert XML tags <a href...>, but here we just
        identify them for now).
        """
        count = 0
        for sb in blocks:
            if sb.role not in ["body", "list-item"]:
                continue
                
            text = sb.original_block.text
            # Simple check
            matches = self.REF_PATTERN.findall(text)
            if matches:
                # We found references.
                # In a real conversion pipeline, we would wrap them in semantic tags here.
                # For structural analysis, we just log/metadata them.
                if "footnote_refs" not in sb.metadata:
                     sb.metadata["footnote_refs"] = []
                sb.metadata["footnote_refs"].extend(matches)
                count += len(matches)
                
        return blocks
