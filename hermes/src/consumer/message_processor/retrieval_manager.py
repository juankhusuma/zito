from src.common.supabase_client import client as supabase
from ...model.search import Questions
from ...retrieval.retrieval_context import RetrievalContext
from ...retrieval.retrieval_factory import get_retrieval_strategy
from .agent_caller import AgentCaller

class RetrievalManager:
    @staticmethod
    def set_search_state(message_id: str):
        supabase.table("chat").update({"state": "searching"}).eq("id", message_id).execute()

    @staticmethod
    def perform_retrieval(eval_res: Questions, message_id: str) -> list[dict]:
        RetrievalManager.set_search_state(message_id)
        try:
            retrieval_strategy = get_retrieval_strategy(eval_res.classification)
            retrieval_context = RetrievalContext(retrieval_strategy)
            documents = AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    retrieval_context.search, eval_res.questions
                ),
                max_attempts=2,
                base_delay=3,
            )
            return documents if documents else []
        except Exception as e:
            print(f"Search failed: {e}")
            return []
