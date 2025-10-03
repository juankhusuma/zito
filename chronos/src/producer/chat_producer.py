from pydantic import BaseModel
import uuid
import json
import aio_pika
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)

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
        logger.info(f"DEBUG: publish() called, conn={klass.conn}, is_closed={klass.conn.is_closed if klass.conn else 'N/A'}")

        if klass.conn is None or klass.conn.is_closed:
            logger.info("DEBUG: Connection closed, reconnecting...")
            import asyncio
            loop = asyncio.get_running_loop()
            try:
                await klass.connect(loop)
                logger.info("DEBUG: Reconnect successful")
            except Exception as e:
                logger.error(f"DEBUG: Reconnect failed: {e}")
                return {"status": "Error", "message": f"Failed to reconnect: {str(e)}"}

        try:
            logger.info(f"DEBUG: Publishing to queue {klass.publish_queue.name}")
            await klass.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message.model_dump()).encode(),
                    correlation_id=str(uuid.uuid4()),
                ),
                routing_key=klass.publish_queue.name,
            )
            logger.info("DEBUG: Message published successfully")
            return {"status": "Message sent successfully"}
        except Exception as e:
            logger.error(f"DEBUG: Publish failed: {e}")
            return {"status": "Error", "message": str(e)}
    
