from abc import ABC, abstractmethod
from typing import Any, List, Dict

class RetrievalStrategy(ABC):
    @abstractmethod
    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        pass
