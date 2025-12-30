"""EPUB file builder."""

class EPUBBuilder:
    """
    Builds valid EPUB files from structured content.
    
    Responsibilities:
    - Create EPUB3 structure (with EPUB2 compatibility)
    - Generate spine, TOC, metadata
    - Handle footnotes with proper IDs
    - Ensure valid EPUB format
    """
    
    def __init__(self, metadata: dict = None):
        """
        Initialize builder with metadata.
        
        Args:
            metadata: Book metadata (title, author, language, etc.)
        """
        self.metadata = metadata or {}
    
    def build(self, chapters: list, output_path: str) -> str:
        """
        Build EPUB file from chapters.
        
        Args:
            chapters: List of chapter dictionaries with title and content
            output_path: Path for output EPUB file
            
        Returns:
            str: Path to created EPUB file
        """
        raise NotImplementedError("EPUB builder not yet implemented")
