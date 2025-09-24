from pydantic import BaseModel
import uuid
import json
import aio_pika
from dotenv import load_dotenv
import os
load_dotenv()

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

class ChatProducer:
    conn = None
    channel = None
    publish_queue = None

    @classmethod
    async def connect(klass, loop):
        conn =  await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"), loop=loop, login=os.getenv("RABBITMQ_USER"), password=os.getenv("RABBITMQ_PASS"),
        )
        channel = await conn.channel()
        publish_queue_name = 'chat'
        publish_queue = await channel.declare_queue(publish_queue_name)
        klass.conn = conn
        klass.channel = channel
        klass.publish_queue = publish_queue

        return conn
    
    @classmethod
    async def publish(klass, message: History):
        if klass.conn is None or klass.conn.is_closed:
            import asyncio
            loop = asyncio.get_running_loop()
            await klass.connect(loop)

        try:
            await klass.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message.model_dump()).encode(),
                    correlation_id=str(uuid.uuid4()),
                ),
                routing_key=klass.publish_queue.name,
            )
            return {"status": "Message sent successfully"}
        except Exception as e:
            return {"status": "Error", "message": str(e)}
    
