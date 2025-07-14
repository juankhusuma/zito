from ...model.search import History, QnAList, Questions
from ...agents.answering_agent import answer_generated_questions, answer_user
from ...agents.evaluator_agent import evaluate_question
from .agent_caller import AgentCaller
from .retrieval_manager import RetrievalManager

class MessageHandler:
    @staticmethod
    def serialize_message(messages: list[dict]):
        return [
            {
                "role": msg["role"] if msg["role"] != "assistant" else "model",
                "parts": [{"text": msg["content"]}],
            }
            for msg in messages
        ]

    @staticmethod
    def evaluate_question(history: History) -> Questions:
        try:
            return AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(evaluate_question, history),
                max_attempts=3,
                base_delay=2,
            )
        except Exception as e:
            raise Exception(f"Unable to evaluate user question: {e}")

    @staticmethod
    def generate_planned_answers(history: History, documents: list[dict], eval_res: Questions) -> QnAList:
        if not documents:
            return QnAList(is_sufficient=False, answers=[])
        try:
            return AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    answer_generated_questions,
                    history,
                    documents,
                    eval_res,
                ),
                max_attempts=3,
                base_delay=2,
            )
        except Exception as e:
            print(f"Failed to generate answers: {e}")
            return QnAList(is_sufficient=False, answers=[])

    @staticmethod
    def generate_final_response(history: History, documents: list[dict], serialized_answer_res: QnAList, message_id: str):
        try:
            AgentCaller.retry_with_exponential_backoff(
                lambda: AgentCaller.safe_agent_call(
                    answer_user,
                    history,
                    documents,
                    serialized_answer_res,
                    message_id,
                ),
                max_attempts=4,
                base_delay=2,
                max_delay=15,
            )
        except Exception as e:
            raise Exception(f"Unable to generate response: {e}")
