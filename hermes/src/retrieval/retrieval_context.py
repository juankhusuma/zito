from .retrieval_strategy import RetrievalStrategy
from typing import List, Dict, Any

class RetrievalContext:
    def __init__(self, strategy: RetrievalStrategy):
        self._strategy = strategy

    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        return self._strategy.search(questions)
