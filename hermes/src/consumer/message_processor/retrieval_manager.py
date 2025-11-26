from concurrent.futures import ThreadPoolExecutor
from src.common.supabase_client import client as supabase
from src.utils.logger import HermesLogger
from ...model.search import Questions
from ...retrieval.retrieval_context import RetrievalContext
from ...retrieval.retrieval_factory import get_retrieval_strategy
from .agent_caller import AgentCaller
from ...retrieval.kuhper_retrieval import KuhperRetrievalStrategy
from ...retrieval.legal_document_retrieval import LegalDocumentRetrievalStrategy
from ...retrieval.undang_undang_retrieval import UndangUndangRetrievalStrategy
from ...retrieval.perpres_retrieval import PerpresRetrievalStrategy

logger = HermesLogger("retrieval")

class RetrievalManager:
    @staticmethod
    def set_search_state(message_id: str):
        try:
            supabase.table("chat").update({"state": "searching"}).eq("id", message_id).execute()
            logger.debug("Search state updated", message_id=message_id)
        except Exception as e:
            logger.warning("Failed to update search state", message_id=message_id, error=str(e))

    @staticmethod
    def perform_retrieval(eval_res: Questions, message_id: str) -> list[dict]:
        RetrievalManager.set_search_state(message_id)
        try:
            uu_retrieval = UndangUndangRetrievalStrategy()
            kuhper_retrieval = KuhperRetrievalStrategy()
            legal_doc_retrieval = LegalDocumentRetrievalStrategy()
            perpres_retrieval = PerpresRetrievalStrategy()
            logger.debug("Retrieval strategies initialized")

            # Define wrapper functions to avoid lambda closure issues
            def call_uu_retrieval():
                return AgentCaller.retry_with_exponential_backoff(
                    lambda: AgentCaller.safe_agent_call(
                        uu_retrieval.search, eval_res.questions
                    ),
                    max_attempts=2,
                    base_delay=3,
                )

            def call_kuhper_retrieval():
                return AgentCaller.retry_with_exponential_backoff(
                    lambda: AgentCaller.safe_agent_call(
                        kuhper_retrieval.search, eval_res.questions
                    ),
                    max_attempts=2,
                    base_delay=3,
                )

            # DISABLED: KUHP index does not exist in Elasticsearch yet
            # TODO: Re-enable after KUHP documents are indexed
            # def call_kuhp_retrieval():
            #     return AgentCaller.retry_with_exponential_backoff(
            #         lambda: AgentCaller.safe_agent_call(
            #             kuhp_retrieval.search, eval_res.questions
            #         ),
            #         max_attempts=2,
            #         base_delay=3,
            #     )

            def call_legal_doc_retrieval():
                return AgentCaller.retry_with_exponential_backoff(
                    lambda: AgentCaller.safe_agent_call(
                        legal_doc_retrieval.search, eval_res.questions
                    ),
                    max_attempts=2,
                    base_delay=3,
                )

            def call_perpres_retrieval():
                return AgentCaller.retry_with_exponential_backoff(
                    lambda: AgentCaller.safe_agent_call(
                        perpres_retrieval.search, eval_res.questions
                    ),
                    max_attempts=2,
                    base_delay=3,
                )

            with ThreadPoolExecutor(max_workers=4) as executor:  # Reduced to 4 workers (KUHP disabled)
                # Submit all four retrieval tasks concurrently (KUHP disabled until index exists)
                uu_future = executor.submit(call_uu_retrieval)
                kuhper_future = executor.submit(call_kuhper_retrieval)
                # DISABLED: KUHP retrieval until index exists
                # kuhp_future = executor.submit(call_kuhp_retrieval)
                legal_doc_future = executor.submit(call_legal_doc_retrieval)
                perpres_future = executor.submit(call_perpres_retrieval)  # ✅ NEW: Perpres retrieval

                # Wait for all results
                uu_documents = uu_future.result() or []
                kuhper_documents = kuhper_future.result() or []
                # DISABLED: KUHP retrieval until index exists
                # kuhp_documents = kuhp_future.result()
                kuhp_documents = []  # Return empty list instead
                legal_doc_documents = legal_doc_future.result() or []
                perpres_documents = perpres_future.result() or []

            all_documents = uu_documents + kuhper_documents + kuhp_documents + legal_doc_documents + perpres_documents
            logger.info(
                "Retrieval complete",
                total=len(all_documents),
                uu=len(uu_documents),
                kuhper=len(kuhper_documents),
                kuhp=len(kuhp_documents),
                legal_doc=len(legal_doc_documents),
                perpres=len(perpres_documents)
            )
            return all_documents if all_documents else []
        except Exception as e:
            logger.error("Retrieval failed", error=str(e))
            import traceback
            traceback.print_exc()
            return []
