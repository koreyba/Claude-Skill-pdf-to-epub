from abc import ABC, abstractmethod
from typing import List
from conversion.detectors.models import TextBlock

class BlockSorter(ABC):
    @abstractmethod
    def sort_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        Sorts a list of text blocks closer to reading order.
        """
        pass
