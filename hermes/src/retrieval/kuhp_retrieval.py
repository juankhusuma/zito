from typing import List, Dict, Any
from .retrieval_strategy import RetrievalStrategy
from ..agents.search_kuhp_agent import generate_and_execute_es_query_kuhp

class KuhpRetrievalStrategy(RetrievalStrategy):
    def search(self, questions: List[str]) -> List[Dict[str, Any]]:
        s_documents, d_documents = generate_and_execute_es_query_kuhp(questions)
        return s_documents + d_documents
