from src.common.supabase_client import client as supabase
from ...model.search import Questions
from ...retrieval.retrieval_context import RetrievalContext
from ...retrieval.retrieval_factory import get_retrieval_strategy
from .agent_caller import AgentCaller
from ...retrieval.kuhp_retrieval import KuhpRetrievalStrategy
from ...retrieval.kuhper_retrieval import KuhperRetrievalStrategy
from ...retrieval.legal_document_retrieval import LegalDocumentRetrievalStrategy
from ...retrieval.undang_undang_retrieval import UndangUndangRetrievalStrategy

class RetrievalManager:
    @staticmethod
    def set_search_state(message_id: str):
        supabase.table("chat").update({"state": "searching"}).eq("id", message_id).execute()

    @staticmethod
    def perform_retrieval(eval_res: Questions, message_id: str) -> list[dict]:
        RetrievalManager.set_search_state(message_id)
        try:
            # retrieval_strategy = get_retrieval_strategy(eval_res.classification)
            # retrieval_context = RetrievalContext(retrieval_strategy)
            uu_retrieval = UndangUndangRetrievalStrategy()
            kuhper_retrieval = KuhperRetrievalStrategy()
            kuhp_retrieval = KuhpRetrievalStrategy()
            all_retrievals = LegalDocumentRetrievalStrategy()

            uu_documents = AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    uu_retrieval.search, eval_res.questions
                ),
                max_attempts=2,
                base_delay=3,
            )

            kuhper_documents = AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    kuhper_retrieval.search, eval_res.questions
                ),
                max_attempts=2,
                base_delay=3,
            )

            kuhp_documents = AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    kuhp_retrieval.search, eval_res.questions
                ),
                max_attempts=2,
                base_delay=3,
            )

            all_documents = AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    all_retrievals.search, eval_res.questions
                ),
                max_attempts=2,
                base_delay=3,
            )
            
            all_documents = uu_documents + kuhper_documents + kuhp_documents + all_documents
            return all_documents if all_documents else []
        except Exception as e:
            print(f"Search failed: {e}")
            return []
