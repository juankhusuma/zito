from .retrieval_strategy import RetrievalStrategy
from .kuhp_retrieval import KuhpRetrievalStrategy
from .legal_document_retrieval import LegalDocumentRetrievalStrategy

def get_retrieval_strategy(classification: str) -> RetrievalStrategy:
    if classification == "kuhp":
        return KuhpRetrievalStrategy()
    else:
        return LegalDocumentRetrievalStrategy()
