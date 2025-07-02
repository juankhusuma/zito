
import aio_pika
from src.common.supabase_client import client as supabase
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import json
import traceback

from ..model.search import History, QnAList
from ..agents.answering_agent import answer_generated_questions, answer_user
from ..agents.evaluator_agent import evaluate_question
from ..agents.search_agent import generate_and_execute_es_query
from ..agents.search_kuhp_agent import generate_and_execute_es_query_kuhp
from ..agents.title_agent import generate_title

load_dotenv()

class ChatConsumer:
    @staticmethod
    async def consume(loop):
        conn = await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            loop=loop,
            login=os.getenv("RABBITMQ_USER"),
            password=os.getenv("RABBITMQ_PASS"),
        )
        channel = await conn.channel()
        queue = await channel.declare_queue("chat")
        await queue.consume(ChatConsumer.process_message, no_ack=False)
        return conn

    @staticmethod
    def __serialize_message(messages: list[dict]):
        return [
            {
                "role": msg["role"] if msg["role"] != "assistant" else "model",
                "parts": [{"text": msg["content"]}],
            }
            for msg in messages
        ]

    @staticmethod
    def __init_message(session_uid: str, user_uid: str):
        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", session_uid).execute()
        message_ref = (
            supabase.table("chat")
            .insert({
                "role": "assistant",
                "content": "",
                "session_uid": session_uid,
                "user_uid": user_uid,
                "state": "loading",
            })
            .execute()
        )
        return message_ref

    @staticmethod
    def __set_search_state(message_id: str):
        supabase.table("chat").update({"state": "searching"}).eq("id", message_id).execute()

    @staticmethod
    def __retry_with_exponential_backoff(
        func,
        max_attempts=3,
        base_delay=1,
        max_delay=10,
        *args,
        **kwargs,
    ):
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"Final attempt failed for {func.__name__}: {str(e)}")
                    raise e

                delay = min(base_delay * (2**attempt), max_delay)
                print(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s..."
                )
                time.sleep(delay)

        raise Exception(f"All {max_attempts} attempts failed for {func.__name__}")

    @staticmethod
    def __safe_agent_call(agent_func, *args, **kwargs):
        try:
            return agent_func(*args, **kwargs)
        except Exception as e:
            print(f"{agent_func.__name__} error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e

    @staticmethod
    async def process_message(message):
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        history = ChatConsumer.__serialize_message(body["messages"])
        is_new = len(history) == 1
        supabase.auth.set_session(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
        )

        message_ref = None

        try:
            if is_new:
                try:
                    title = ChatConsumer.__retry_with_exponential_backoff(
                        generate_title, max_attempts=2, history=history
                    )
                    supabase.table("session").update({
                        "title": title.replace("*", "").replace("#", "").replace("`", ""),
                        "last_updated_at": datetime.now().isoformat(),
                    }).eq("id", body["session_uid"]).execute()
                except Exception as e:
                    print(f"Failed to generate title: {str(e)}")

            message_ref = ChatConsumer.__init_message(
                body["session_uid"], body["user_uid"]
            )
            message_id = message_ref.data[0]["id"]
            documents = []

            try:
                eval_res = ChatConsumer.__retry_with_exponential_backoff(
                    lambda: ChatConsumer.__safe_agent_call(evaluate_question, history),
                    max_attempts=3,
                    base_delay=2,
                )
            except Exception as e:
                raise Exception(f"Unable to evaluate user question: {e}")

            serialized_answer_res = QnAList(is_sufficient=False, answers=[])

            if not eval_res.is_sufficient:
                ChatConsumer.__set_search_state(message_id)
                if eval_res.classification == "kuhp":
                    print("📄 SEARCHING KUHP INDEX")
                    s_documents, d_documents = ChatConsumer.__retry_with_exponential_backoff(
                        lambda: ChatConsumer.__safe_agent_call(
                            generate_and_execute_es_query_kuhp, eval_res.questions
                        ),
                        max_attempts=2,
                        base_delay=3,
                    )
                    documents = s_documents + d_documents
                    serialized_answer_res = ChatConsumer.__retry_with_exponential_backoff(
                                lambda: ChatConsumer.__safe_agent_call(
                                    answer_generated_questions,
                                    history,
                                    documents,
                                    eval_res,
                                ),
                                max_attempts=3,
                                base_delay=2,
                            )
                else:
                    try:
                        documents = ChatConsumer.__retry_with_exponential_backoff(
                            lambda: ChatConsumer.__safe_agent_call(
                                generate_and_execute_es_query, eval_res.questions
                            ),
                            max_attempts=2,
                            base_delay=3,
                        )
                        if not documents:
                            documents = []
                    except Exception as e:
                        print(f"Search failed: {e}")
                        documents = []

                    if documents:
                        try:
                            serialized_answer_res = ChatConsumer.__retry_with_exponential_backoff(
                                lambda: ChatConsumer.__safe_agent_call(
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

            try:
                ChatConsumer.__retry_with_exponential_backoff(
                    lambda: ChatConsumer.__safe_agent_call(
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

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(error_msg)
            print(f"Full traceback: {traceback.format_exc()}")

            if message_ref:
                try:
                    supabase.table("chat").update({
                        "content": "Terjadi isu saat menjawab pertanyaan anda, silakan coba ajukan pertanyaan anda kembali🙏",
                        "state": "error",
                    }).eq("id", message_ref.data[0]["id"]).execute()
                except Exception as db_error:
                    print(f"Failed to update error state in database: {str(db_error)}")

            return {"status": "Error processing message", "error": str(e)}

        return {"status": "Message sent successfully"}
