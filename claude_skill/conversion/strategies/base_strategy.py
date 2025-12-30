"""Base class for conversion strategies."""

class BaseStrategy:
    """
    Base conversion strategy.
    
    Defines the interface for all conversion strategies (simple, academic, nonfiction).
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize strategy with optional configuration.
        
        Args:
            config: Configuration dictionary for the strategy
        """
        self.config = config or {}
    
    def convert(self, pdf_path: str, output_path: str) -> dict:
        """
        Convert PDF to EPUB.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output EPUB file
            
        Returns:
            dict: Conversion result with status and metadata
        """
        raise NotImplementedError("Subclasses must implement convert()")
