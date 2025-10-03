import aio_pika
import os
import json
from dotenv import load_dotenv
from src.common.supabase_client import client as supabase
from .message_processor.message_handler import MessageHandler
from .message_processor.session_manager import SessionManager
from .message_processor.retrieval_manager import RetrievalManager
from .message_processor.error_handler import ErrorHandler
from ..model.search import QnAList

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
        print("DEBUG: RabbitMQ consumer started and waiting for messages...")

        # Keep the consumer running indefinitely
        try:
            import asyncio
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            print("DEBUG: RabbitMQ consumer shutting down...")
            await conn.close()
            raise

    @staticmethod
    async def process_message(message):
        print("DEBUG: process_message called!!!")
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        print(f"DEBUG: Message body: {body}")
        message_ref = None
        try:
            history = MessageHandler.serialize_message(body["messages"])
            is_new = len(history) == 1
            supabase.auth.set_session(
                access_token=body["access_token"],
                refresh_token=body["refresh_token"],
            )

            if is_new:
                SessionManager.handle_new_chat(history, body["session_uid"])

            print(f"DEBUG: About to call init_message for session: {body['session_uid']}")
            message_ref = SessionManager.init_message(
                body["session_uid"], body["user_uid"]
            )
            message_id = message_ref.data[0]["id"]
            print(f"DEBUG: Got message_id: {message_id}")
            
            eval_res = MessageHandler.evaluate_question(history)
            
            documents = []
            serialized_answer_res = QnAList(is_sufficient=False, answers=[])

            if not eval_res.is_sufficient or True:
                documents = RetrievalManager.perform_retrieval(eval_res, message_id)
                serialized_answer_res = MessageHandler.generate_planned_answers(history, documents, eval_res)

            MessageHandler.generate_final_response(history, documents, serialized_answer_res, message_id)

            # Store thinking duration after processing is complete
            SessionManager.finalize_message_with_thinking_duration(message_id)

        except Exception as e:
            return ErrorHandler.handle_error(e, message_ref)

        return {"status": "Message sent successfully"}
