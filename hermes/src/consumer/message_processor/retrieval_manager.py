from concurrent.futures import ThreadPoolExecutor
from src.common.supabase_client import client as supabase
from ...model.search import Questions
from ...retrieval.retrieval_context import RetrievalContext
from ...retrieval.retrieval_factory import get_retrieval_strategy
from .agent_caller import AgentCaller
# DISABLED: KUHP index does not exist in Elasticsearch yet
# TODO: Re-enable after KUHP documents are indexed
# from ...retrieval.kuhp_retrieval import KuhpRetrievalStrategy
from ...retrieval.kuhper_retrieval import KuhperRetrievalStrategy
from ...retrieval.legal_document_retrieval import LegalDocumentRetrievalStrategy
from ...retrieval.undang_undang_retrieval import UndangUndangRetrievalStrategy
from ...retrieval.perpres_retrieval import PerpresRetrievalStrategy

class RetrievalManager:
    @staticmethod
    def set_search_state(message_id: str):
        try:
            print(f"DEBUG: Updating search state for message_id: {message_id}")
            supabase.table("chat").update({"state": "searching"}).eq("id", message_id).execute()
            print(f"DEBUG: Search state updated successfully")
        except Exception as e:
            # Don't let state update failure block the entire retrieval process
            print(f"WARNING: Failed to update search state for {message_id}: {e}")
            print("WARNING: Continuing with retrieval anyway...")

    @staticmethod
    def perform_retrieval(eval_res: Questions, message_id: str) -> list[dict]:
        print("DEBUG: perform_retrieval started")
        RetrievalManager.set_search_state(message_id)
        try:
            # retrieval_strategy = get_retrieval_strategy(eval_res.classification)
            # retrieval_context = RetrievalContext(retrieval_strategy)
            print("DEBUG: Initializing retrieval strategies...")
            uu_retrieval = UndangUndangRetrievalStrategy()
            kuhper_retrieval = KuhperRetrievalStrategy()
            # DISABLED: KUHP index does not exist in Elasticsearch yet
            # TODO: Re-enable after KUHP documents are indexed
            # kuhp_retrieval = KuhpRetrievalStrategy()
            legal_doc_retrieval = LegalDocumentRetrievalStrategy()  # ✅ RE-ENABLED: peraturan_indonesia index now exists
            perpres_retrieval = PerpresRetrievalStrategy()  # ✅ NEW: perpres index for presidential regulations
            print("DEBUG: Strategies initialized")

            # Parallelize all five index searches for improved speed
            print("DEBUG: Calling ALL retrievals in PARALLEL...")

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

            print(f"DEBUG: UU retrieval done, got {len(uu_documents)} documents")
            print(f"DEBUG: KUHPER retrieval done, got {len(kuhper_documents)} documents")
            print(f"DEBUG: KUHP retrieval done, got {len(kuhp_documents)} documents")
            print(f"DEBUG: Legal Doc retrieval done, got {len(legal_doc_documents)} documents")
            print(f"DEBUG: Perpres retrieval done, got {len(perpres_documents)} documents")

            # Combine results from all indices
            print("DEBUG: Combining results...")
            all_documents = uu_documents + kuhper_documents + kuhp_documents + legal_doc_documents + perpres_documents
            print(f"DEBUG: perform_retrieval done, returning {len(all_documents)} total documents")
            return all_documents if all_documents else []
        except Exception as e:
            print(f"DEBUG: perform_retrieval exception: {e}")
            print(f"Search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
