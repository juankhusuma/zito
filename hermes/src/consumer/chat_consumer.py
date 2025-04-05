from pydantic import BaseModel
import aio_pika
from src.common.gemini_client import client as gemini_client
from src.common.supabase_client import get_client
from dotenv import load_dotenv
import os
from google.genai import types
load_dotenv()
import json

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
        print(f"host: {os.getenv('RABBITMQ_HOST', 'localhost')}")
        print(f"user: {os.getenv('RABBITMQ_USER')}")
        print(f"password: {os.getenv('RABBITMQ_PASS')}")
        conn =  await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"), loop=loop, login=os.getenv("RABBITMQ_USER"), password=os.getenv("RABBITMQ_PASS")
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

        supabase = await get_client()
        msg = ""
        await supabase.auth.set_session(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
        )
        message_ref = await supabase.from_("chat").insert({
            "role": "assistant",
            "content": "",
            "session_uid": body["session_uid"],
            "user_uid": body["user_uid"],
        }).execute()
    
        res = gemini_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction="Generate a response to the user message, respond in a friendly and helpful manner.",
            ),
        )
        for chunk in res:
            msg += chunk.text
            res = await supabase.table("chat").update({"content": msg}).eq("id", message_ref.data[0]["id"]).execute()

        await supabase.from_("chat").update({"content": msg}).eq("id", message_ref.data[0]["id"]).execute()
        return {"status": "Message sent successfully"}
            

