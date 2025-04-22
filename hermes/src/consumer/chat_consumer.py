from pydantic import BaseModel
import aio_pika
from src.common.gemini_client import client as gemini_client
from src.common.supabase_client import client as supabase
from dotenv import load_dotenv
import os
from google.genai import types
from ..config.llm import CHATBOT_SYSTEM_PROMPT, MODEL_NAME
from ..tools.search_legal_document import legal_document_search, get_schema_information, example_queries
from datetime import datetime
load_dotenv()
import httpx
import json
import re
from pydantic import BaseModel
import asyncio
from collections import defaultdict
import time

class CheckMessage(BaseModel):
    need_retrieval: bool
    queries: list[str]

class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: str

class History(BaseModel):
    messages: list[ChatMessage]
    session_uid: str
    user_uid: str
    access_token: str
    refresh_token: str

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
    async def process_message(message):
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        history = ChatConsumer.__serialize_message(body["messages"])
        print(history)
        is_new = len(history) == 1
        msg = ""
        supabase.auth.set_session(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
        )

        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", body["session_uid"]).execute()

        try:
            message_ref = supabase.table("chat").insert({
                "role": "assistant",
                "content": "",
                "session_uid": body["session_uid"],
                "user_uid": body["user_uid"],
                "state": "loading",
            }).execute()

            res = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=CHATBOT_SYSTEM_PROMPT,
                    tools=[
                        legal_document_search,
                        get_schema_information,
                        example_queries,
                    ],
                ),
            )

            supabase.table("chat").update({
                "content": res.candidates[0].content.parts[0].text,
                "state": "done",
            }).eq("id", message_ref.data[0]["id"]).execute()

            if is_new:
                try:
                    res = gemini_client.models.generate_content_stream(
                        model="gemini-2.0-flash-lite",
                        contents=history,
                        config=types.GenerateContentConfig(
                            system_instruction="""
                            A title for the chat session, given the context of the chat, 
                            just a sentence with a few words will do.
                            Focus on the content of the chat, and make it as short as possible.
                            Instead of "Pembahasan isi UU No. 1 Tahun 2021", you can just say "UU No. 1 Tahun 2021: Pembahasan"
                            """,
                            max_output_tokens=500,
                        ),
                    )
                    title = ""
                    for chunk in res:
                        try:
                            if chunk.candidates[0].content and chunk.candidates[0].content.parts:
                                title += "".join([part.text for part in chunk.candidates[0].content.parts])
                        except (IndexError, AttributeError) as e:
                            print(f"Error processing title chunk: {str(e)}")
                            continue
                    
                    if title:
                        supabase.table("session").update({
                            "title": title.replace("*", "").replace("#", "").replace("`", ""),
                        }).eq("id", body["session_uid"]).execute()
                        print(f"Chat session title: {title}")
                    else:
                        # Set a default title if title generation fails
                        supabase.table("session").update({
                            "title": "New Conversation",
                        }).eq("id", body["session_uid"]).execute()
                        
                except Exception as e:
                    print(f"Error generating title: {str(e)}")
                    # Set a default title if title generation fails completely
                    supabase.table("session").update({
                        "title": "New Conversation",
                    }).eq("id", body["session_uid"]).execute()
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            supabase.table("chat").update({
                "content": "Terjadi isu saat menjawab pertanyaan anda, silakan coba ajukan pertanyaan anda kembali🙏",
                "state": "done",
            }).eq("id", message_ref.data[0]["id"]).execute()
            return {"status": "Error processing message"}

        return {"status": "Message sent successfully"}