import aio_pika
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from src.common.supabase_client import client as supabase
from src.utils.logger import HermesLogger
from .message_processor.message_handler import MessageHandler
from .message_processor.session_manager import SessionManager
from .message_processor.retrieval_manager import RetrievalManager
from .message_processor.error_handler import ErrorHandler
from ..model.search import QnAList

load_dotenv()
logger = HermesLogger("consumer")

class ChatConsumer:
    # Store channel as class variable for retry logic
    _channel = None

    @staticmethod
    async def consume(loop):
        conn = await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            loop=loop,
            login=os.getenv("RABBITMQ_USER"),
            password=os.getenv("RABBITMQ_PASS"),
        )
        ChatConsumer._channel = await conn.channel()
        await ChatConsumer._channel.set_qos(prefetch_count=3)  # Allow parallel processing of up to 3 messages
        queue = await ChatConsumer._channel.declare_queue("chat")
        await queue.consume(ChatConsumer.process_message, no_ack=False)
        logger.info("RabbitMQ consumer started")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("RabbitMQ consumer shutting down")
            await conn.close()
            raise

    @staticmethod
    async def process_message(message):
        body = json.loads(message.body.decode("utf-8"))
        message_ref = None

        retry_count = body.get('__retry_count', 0)
        MAX_RETRIES = 3
        logger.debug("Processing message", session_uid=body.get("session_uid"), retry=f"{retry_count}/{MAX_RETRIES}")

        try:
            # Wrap entire processing in 5-minute timeout
            async with asyncio.timeout(300):  # 5 minutes = 300 seconds
                history = MessageHandler.serialize_message(body["messages"])
                is_new = len(history) == 1
                supabase.auth.set_session(
                    access_token=body["access_token"],
                    refresh_token=body["refresh_token"],
                )

                message_id = body.get("message_id")
                if not message_id:
                    message_ref = SessionManager.init_message(
                        body["session_uid"], body["user_uid"]
                    )
                    if isinstance(message_ref, dict) and "data" in message_ref and message_ref["data"]:
                        message_id = message_ref["data"][0]["id"]
                    elif hasattr(message_ref, "data") and message_ref.data:
                        message_id = message_ref.data[0]["id"]
                    else:
                        raise Exception("Failed to get message_id from init_message response")

                if is_new:
                    from concurrent.futures import ThreadPoolExecutor
                    logger.debug("New chat detected, running title generation and question evaluation in parallel", message_id=message_id)

                    with ThreadPoolExecutor(max_workers=2) as executor:
                        title_future = executor.submit(SessionManager.handle_new_chat, history, body["session_uid"])
                        eval_future = executor.submit(MessageHandler.evaluate_question, history)

                        title_future.result()
                        eval_res = eval_future.result()
                else:
                    logger.debug("Evaluating question", message_id=message_id)
                    eval_res = MessageHandler.evaluate_question(history)

                documents = []
                serialized_answer_res = QnAList(is_sufficient=False, answers=[])

                if not eval_res.is_sufficient or True:
                    logger.debug("Starting retrieval", message_id=message_id)
                    documents = RetrievalManager.perform_retrieval(eval_res, message_id)
                    logger.debug("Retrieval complete", documents=len(documents))

                    serialized_answer_res = MessageHandler.generate_planned_answers(history, documents, eval_res)

                MessageHandler.generate_final_response(history, documents, serialized_answer_res, message_id)
                SessionManager.finalize_message_with_thinking_duration(message_id)

                await message.ack()
                logger.info("Message processed successfully", session_uid=body['session_uid'])

        except asyncio.TimeoutError:
            logger.error(f"Processing timeout (5 min) for session {body.get('session_uid')}")
            # Don't requeue timeout messages
            await message.nack(requeue=False)
            if message_ref:
                ErrorHandler.handle_error(
                    Exception("Processing timeout after 5 minutes"),
                    message_ref
                )

        except Exception as e:
            logger.error(f"Processing error for session {body.get('session_uid')}: {e}")
            
            # Check if max retries reached
            if retry_count >= MAX_RETRIES:
                logger.error(f"Max retries ({MAX_RETRIES}) reached for session {body.get('session_uid')}. Message rejected.")
                # Don't requeue, message rejected permanently
                await message.nack(requeue=False)
                
                # Mark message as failed in database
                if message_ref:
                    try:
                        # Handle message_ref structure which might be a dict or object
                        message_id = None
                        if isinstance(message_ref, dict) and "data" in message_ref and message_ref["data"]:
                            message_id = message_ref["data"][0]["id"]
                        elif hasattr(message_ref, "data") and message_ref.data:
                            message_id = message_ref.data[0]["id"]
                        
                        if message_id:
                            supabase.table("chat").update({
                                "state": "failed",
                                "content": f"Processing failed after {MAX_RETRIES} retries: {str(e)}"
                            }).eq("id", message_id).execute()
                            logger.info(f"Message {message_id} marked as failed in database")
                    except Exception as db_error:
                        logger.error(f"Failed to update failed message in DB: {db_error}")
            else:
                logger.warning(f"Retry {retry_count + 1}/{MAX_RETRIES} for session {body.get('session_uid')}")

                # Republish with incremented retry count
                try:
                    # Update retry count in body
                    body['__retry_count'] = retry_count + 1

                    # Publish new message with retry count using stored channel
                    await ChatConsumer._channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(body).encode('utf-8'),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                        ),
                        routing_key='chat'
                    )

                    # Acknowledge original message
                    await message.ack()
                    logger.info(f"Message republished with retry count {retry_count + 1}")

                except Exception as republish_error:
                    logger.error(f"Failed to republish message: {republish_error}")
                    # Fallback: simple requeue
                    await message.nack(requeue=True)
            
            if message_ref:
                ErrorHandler.handle_error(e, message_ref)

        return {"status": "Message processing attempted"}
