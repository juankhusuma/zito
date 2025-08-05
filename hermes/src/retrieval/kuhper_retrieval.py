from typing import List, Dict, Any
from .retrieval_strategy import RetrievalStrategy
from ..agents.search_kuhper_agent import generate_and_execute_es_query_kuhper

class KuhperRetrievalStrategy(RetrievalStrategy):
    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        s_documents, d_documents = generate_and_execute_es_query_kuhper(questions)
        return s_documents + d_documents