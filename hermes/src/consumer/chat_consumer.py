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

load_dotenv()
import json
from ..model.search import History, Questions, QnAList

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
    def __answer_user(history: History, documents: list[dict], serialized_answer_res: QnAList):
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
        return gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
            ),
        )

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
        if is_new:
            title = ChatConsumer.__generate_title(history)
            supabase.table("session").update({
                "title": title.replace("*", "").replace("#", "").replace("`", ""),
                "last_updated_at": datetime.now().isoformat(),
            }).eq("id", body["session_uid"]).execute()

        try:
            message_ref = ChatConsumer.__init_message(body["session_uid"], body["user_uid"])
            documents = []
            attempt = 3
            while attempt > 0:
                attempt -= 1
                try:
                    serilized_check_res = ChatConsumer.__init_evaluation(history)
                    break
                except Exception as e:
                    print(f"Error generating question: {str(e)}")
                    time.sleep(2)
                    continue
            serialized_answer_res = QnAList(
                is_sufficient=False,
                answers=[],
            )

            print(serilized_check_res)
            if not serilized_check_res.is_sufficient:
                print("Setting search state")
                ChatConsumer.__set_search_state(message_ref.data[0]["id"])
                documents = ChatConsumer.__generate_and_execute_es_query(serilized_check_res.questions)
                attempt = 3
                while attempt > 0:
                    attempt -= 1
                    try:
                        serialized_answer_res = ChatConsumer.__answer_generated_questions(history, documents, serilized_check_res)
                        break
                    except Exception as e:
                        print(f"Error generating answer: {str(e)}")
                        time.sleep(2)
                        continue
                print(serialized_answer_res)
                attempt = 3
                while attempt > 0:
                    attempt -= 1
                    try:
                        res = ChatConsumer.__answer_user(history, documents, serialized_answer_res)
                        break
                    except Exception as e:
                        print(f"Error generating answer: {str(e)}")
                        time.sleep(2)
                        continue
                supabase.table("chat").update({
                    "content": res.text,
                    "state": "done",
                    "documents": json.dumps(documents, indent=2),
                }).eq("id", message_ref.data[0]["id"]).execute()

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            supabase.table("chat").update({
                "content": "Terjadi isu saat menjawab pertanyaan anda, silakan coba ajukan pertanyaan anda kembali🙏",
                "state": "error",
            }).eq("id", message_ref.data[0]["id"]).execute()
            return {"status": "Error processing message"}

        return {"status": "Message sent successfully"}