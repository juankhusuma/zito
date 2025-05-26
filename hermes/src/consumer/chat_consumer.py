from pydantic import BaseModel
import aio_pika
from src.common.gemini_client import client as gemini_client
from src.common.supabase_client import client as supabase
from dotenv import load_dotenv
import os
from google.genai import types
import time
from ..config.llm import CHATBOT_SYSTEM_PROMPT, \
                        MODEL_NAME, SEARCH_AGENT_PROMPT, \
                        EVALUATOR_AGENT_PROMPT_INIT, ANSWERING_AGENT_PROMPT, \
                        GENERATE_TITLE_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.search_legal_document import legal_document_search
from datetime import datetime
import json
import asyncio

load_dotenv()
import json
from ..model.search import History, Questions, QnAList
import traceback

class ChatConsumer:
    @staticmethod
    async def consume(loop):
        conn =  await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"), loop=loop, login=os.getenv("RABBITMQ_USER"), password=os.getenv("RABBITMQ_PASS"),
        )
        channel = await conn.channel()
        queue = await channel.declare_queue("chat")
        await queue.consume(ChatConsumer.process_message, no_ack=False)
        return conn
    
    @staticmethod
    def __serialize_message(messages: History):
        history = []
        for msg in messages:
            history.append(
                {
                    "role": msg["role"] if msg["role"] != "assistant" else "model",
                    "parts": [
                        {
                            "text": msg["content"],
                        }
                    ],
                }
            )
        return history

    @staticmethod
    def __init_message(session_uid: str, user_uid: str):
        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", session_uid).execute()
        message_ref = supabase.table("chat").insert({
            "role": "assistant",
            "content": "",
            "session_uid": session_uid,
            "user_uid": user_uid,
            "state": "loading",
        }).execute()
        return message_ref
    
    @staticmethod
    def __init_evaluation(history: History):
        check_res = gemini_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=EVALUATOR_AGENT_PROMPT_INIT,
                response_mime_type="application/json",
                response_schema=Questions,
                temperature=0.2,
            ),
        )
        return Questions.model_validate(check_res.parsed)
        
    @staticmethod
    def __answer_user(history: History, documents: list[dict], serialized_answer_res: QnAList, message_id: str = None):
        time.sleep(1)
        context = history
        if len(documents) > 0 and len(serialized_answer_res.answers) > 0:
            context = history + [{
                "role": "user",
                "parts": [
                    {
                        "text": serialized_answer_res.model_dump_json(),
                    }
                ],
            }] + [{
                "role": "assistant",
                "parts": [
                    {
                        "text": json.dumps(documents, indent=2) if documents else "",
                    },
                ],
            }]
        
        # Use streaming generation
        if message_id:
            return ChatConsumer.__stream_answer_user(context, message_id, documents)
        else:
            return gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=context,
                config=types.GenerateContentConfig(
                    system_instruction=CHATBOT_SYSTEM_PROMPT,
                ),
            )

    @staticmethod
    def __stream_answer_user(context: History, message_id: str, documents: list[dict]):
        """Stream the response and update the database in real-time"""
        full_content = ""
        
        try:
            # Generate streaming response
            stream = gemini_client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=context,
                config=types.GenerateContentConfig(
                    system_instruction=CHATBOT_SYSTEM_PROMPT,
                ),
            )
            
            # Process each chunk and update database
            for chunk in stream:
                if chunk.text:
                    full_content += chunk.text
                    # Update database with current content
                    try:
                        supabase.table("chat").update({
                            "content": full_content,
                            "state": "streaming",
                        }).eq("id", message_id).execute()
                    except Exception as db_error:
                        print(f"Error updating streaming content: {str(db_error)}")
                        continue
            
            # Final update with complete content
            supabase.table("chat").update({
                "content": full_content,
                "state": "done",
                "documents": json.dumps(documents, indent=2) if documents else "[]",
            }).eq("id", message_id).execute()
            
            # Create a mock response object for compatibility
            class MockResponse:
                def __init__(self, text):
                    self.text = text
            
            return MockResponse(full_content)
            
        except Exception as e:
            print(f"Streaming error: {str(e)}")
            # Fallback to regular generation
            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=context,
                config=types.GenerateContentConfig(
                    system_instruction=CHATBOT_SYSTEM_PROMPT,
                ),
            )
            
            # Update with final content
            supabase.table("chat").update({
                "content": response.text,
                "state": "done",
                "documents": json.dumps(documents, indent=2) if documents else "[]",
            }).eq("id", message_id).execute()
            
            return response

    @staticmethod
    def __answer_generated_questions(history: History, documents: list[dict], serilized_check_res: Questions):
        time.sleep(1)
        answer_res = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=ANSWERING_AGENT_PROMPT(documents, serilized_check_res.questions),
                    response_mime_type="application/json",
                    response_schema=QnAList,
                    temperature=0.2,
                ),
            )
        serialized_answer_res = QnAList.model_validate(answer_res.parsed)
        return serialized_answer_res

    @staticmethod
    def __evaluate_es_query(query: dict):
        try:
            documents = legal_document_search(query=query)
            return (documents, None)
        except Exception as e:
            print(f"Error searching legal documents: {str(e)}")
            return (None, str(e))
    
    @staticmethod
    def __generate_and_execute_es_query(questions: list[str]):
        time.sleep(1)
        last_no_hit = False
        prev_query = None
        max_attempt = 3
        while True and max_attempt > 0:
            max_attempt -= 1
            es_query_res = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=[{
                    "role": "user",
                    "parts": [
                        {
                            "text": "\n".join(["- " + question for question in questions])
                        }
                    ],
                }],
                config=types.GenerateContentConfig(
                    system_instruction=SEARCH_AGENT_PROMPT + \
                        "" if not last_no_hit else REWRITE_PROMPT(prev_query),
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            query_json = None
            try:
                query_json = json.loads(es_query_res.text)
            except json.JSONDecodeError:
                print("Error decoding JSON response from Gemini")
                continue
            documents, error = ChatConsumer.__evaluate_es_query(query_json)
            if len(documents) == 0:
                last_no_hit = True
                continue
            if error is None:
                return documents[:5]
            time.sleep(1)

    @staticmethod
    def __generate_title(history: History):
        title_res = gemini_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=GENERATE_TITLE_AGENT_PROMPT,
                max_output_tokens=500,
            ),
        )
        return title_res.text

    @staticmethod
    def __set_search_state(message_ref: str):
        supabase.table("chat").update({
            "state": "searching",
        }).eq("id", message_ref).execute()

    @staticmethod
    def __retry_with_exponential_backoff(func, max_attempts=3, base_delay=1, max_delay=10, *args, **kwargs):
        """Generic retry mechanism with exponential backoff"""
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:  # Last attempt
                    print(f"Final attempt failed for {func.__name__}: {str(e)}")
                    raise e
                
                delay = min(base_delay * (2 ** attempt), max_delay)
                print(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
        
        raise Exception(f"All {max_attempts} attempts failed for {func.__name__}")

    @staticmethod
    def __safe_init_evaluation(history: History):
        """Wrapper for evaluation with better error handling"""
        try:
            return ChatConsumer.__init_evaluation(history)
        except Exception as e:
            print(f"Evaluation error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e

    @staticmethod
    def __safe_answer_generated_questions(history: History, documents: list[dict], serilized_check_res: Questions):
        """Wrapper for answer generation with better error handling"""
        try:
            return ChatConsumer.__answer_generated_questions(history, documents, serilized_check_res)
        except Exception as e:
            print(f"Answer generation error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e

    @staticmethod
    def __safe_answer_user(history: History, documents: list[dict], serialized_answer_res: QnAList, message_id: str = None):
        """Wrapper for user answer with better error handling"""
        try:
            return ChatConsumer.__answer_user(history, documents, serialized_answer_res, message_id)
        except Exception as e:
            print(f"User answer error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e

    @staticmethod
    async def process_message(message):
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        history = ChatConsumer.__serialize_message(body["messages"])
        print(history)
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
                        ChatConsumer.__generate_title, 
                        max_attempts=2,
                        history=history
                    )
                    supabase.table("session").update({
                        "title": title.replace("*", "").replace("#", "").replace("`", ""),
                        "last_updated_at": datetime.now().isoformat(),
                    }).eq("id", body["session_uid"]).execute()
                except Exception as e:
                    print(f"Failed to generate title: {str(e)}")
                    # Continue processing even if title generation fails

            message_ref = ChatConsumer.__init_message(body["session_uid"], body["user_uid"])
            message_id = message_ref.data[0]["id"]
            documents = []
            
            # Step 1: Evaluation with retry
            try:
                serilized_check_res = ChatConsumer.__retry_with_exponential_backoff(
                    ChatConsumer.__safe_init_evaluation,
                    max_attempts=3,
                    base_delay=2,
                    history=history
                )
            except Exception as e:
                print(f"Failed to evaluate after all retries: {str(e)}")
                raise Exception("Unable to evaluate user question after multiple attempts")

            serialized_answer_res = QnAList(
                is_sufficient=False,
                answers=[],
            )

            print(f"Evaluation result: {serilized_check_res}")
            
            if not serilized_check_res.is_sufficient:
                print("Setting search state")
                ChatConsumer.__set_search_state(message_id)
                
                # Step 2: Search documents with retry
                try:
                    documents = ChatConsumer.__retry_with_exponential_backoff(
                        ChatConsumer.__generate_and_execute_es_query,
                        max_attempts=2,
                        base_delay=3,
                        questions=serilized_check_res.questions
                    )
                    if not documents:
                        print("No documents found after search retries")
                        documents = []
                except Exception as e:
                    print(f"Search failed after all retries: {str(e)}")
                    documents = []  # Continue with empty documents
                
                # Step 3: Generate answers with retry
                if documents:
                    try:
                        serialized_answer_res = ChatConsumer.__retry_with_exponential_backoff(
                            ChatConsumer.__safe_answer_generated_questions,
                            max_attempts=3,
                            base_delay=2,
                            history=history,
                            documents=documents,
                            serilized_check_res=serilized_check_res
                        )
                        print(f"Generated answers: {serialized_answer_res}")
                    except Exception as e:
                        print(f"Failed to generate answers after all retries: {str(e)}")
                        serialized_answer_res = QnAList(is_sufficient=False, answers=[])

            # Step 4: Generate final response with streaming and retry
            try:
                res = ChatConsumer.__retry_with_exponential_backoff(
                    ChatConsumer.__safe_answer_user,
                    max_attempts=4,
                    base_delay=2,
                    max_delay=15,
                    history=history,
                    documents=documents,
                    serialized_answer_res=serialized_answer_res,
                    message_id=message_id
                )
                
                # Content and state are already updated by streaming function
                print("Message processed successfully with streaming")
                
            except Exception as e:
                print(f"Failed to generate final response after all retries: {str(e)}")
                # Update with error state
                supabase.table("chat").update({
                    "content": "Terjadi kesalahan saat memproses respons. Silakan coba lagi.",
                    "state": "error",
                }).eq("id", message_id).execute()
                raise Exception("Unable to generate response after multiple attempts")

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