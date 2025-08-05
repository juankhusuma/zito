from .retrieval_strategy import RetrievalStrategy
from .kuhp_retrieval import KuhpRetrievalStrategy
from .kuhper_retrieval import KuhperRetrievalStrategy
from .legal_document_retrieval import LegalDocumentRetrievalStrategy
from .undang_undang_retrieval import UndangUndangRetrievalStrategy

strategies = {
    "kuhp": KuhpRetrievalStrategy(),
    "kuhper": KuhperRetrievalStrategy(),
    "undang_undang": UndangUndangRetrievalStrategy()
}

def get_retrieval_strategy(classification: str) -> RetrievalStrategy:
    return strategies.get(classification, LegalDocumentRetrievalStrategy())