from typing import List, Dict, Any
from .retrieval_strategy import RetrievalStrategy
from ..agents.search_agent import generate_and_execute_es_query

class LegalDocumentRetrievalStrategy(RetrievalStrategy):
    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        return generate_and_execute_es_query(questions)
