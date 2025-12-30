"""Main conversion orchestrator."""

class Converter:
    """
    Orchestrates PDF to EPUB conversion process.
    
    Workflow:
    1. Extract text blocks from PDF (pdf_extractor)
    2. Order blocks (reading_order)
    3. Detect structure (detectors)
    4. Build EPUB (epub_builder)
    """
    
    def __init__(self, strategy: str = "simple"):
        """
        Initialize converter with strategy.
        
        Args:
            strategy: Conversion strategy to use (simple, academic, nonfiction)
        """
        self.strategy = strategy
    
    def convert(self, pdf_path: str, output_path: str, config: dict = None) -> dict:
        """
        Convert PDF to EPUB.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output EPUB file
            config: Optional conversion configuration
            
        Returns:
            dict: Conversion result with status and log
        """
        raise NotImplementedError("Converter not yet implemented")
