from typing import List, Dict, Any
from .retrieval_strategy import RetrievalStrategy
from ..agents.search_perpres_agent import generate_and_execute_es_query_perpres

class PerpresRetrievalStrategy(RetrievalStrategy):
    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        s_documents, d_documents = generate_and_execute_es_query_perpres(questions)
        return s_documents + d_documents
