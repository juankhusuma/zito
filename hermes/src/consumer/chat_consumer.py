import aio_pika
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from src.common.supabase_client import client as supabase
from .message_processor.message_handler import MessageHandler
from .message_processor.session_manager import SessionManager
from .message_processor.retrieval_manager import RetrievalManager
from .message_processor.error_handler import ErrorHandler
from ..model.search import QnAList

load_dotenv()
logger = logging.getLogger(__name__)

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
        await channel.set_qos(prefetch_count=1)  # Process 1 message at a time
        queue = await channel.declare_queue("chat")
        await queue.consume(ChatConsumer.process_message, no_ack=False)
        print("DEBUG: RabbitMQ consumer started and waiting for messages...", flush=True)
        import sys
        sys.stdout.flush()

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
        body = json.loads(message.body.decode("utf-8"))
        print(f"DEBUG: Message body: {body}")
        message_ref = None
        
        # Track retry count in message body
        retry_count = body.get('__retry_count', 0)
        MAX_RETRIES = 3
        print(f"DEBUG: Retry count: {retry_count}/{MAX_RETRIES}")

        try:
            # Wrap entire processing in 5-minute timeout
            async with asyncio.timeout(300):  # 5 minutes = 300 seconds
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

                print(f"DEBUG: Calling evaluate_question...")
                eval_res = MessageHandler.evaluate_question(history)
                print(f"DEBUG: evaluate_question done")

                documents = []
                serialized_answer_res = QnAList(is_sufficient=False, answers=[])

                if not eval_res.is_sufficient or True:
                    print(f"DEBUG: Calling perform_retrieval...")
                    documents = RetrievalManager.perform_retrieval(eval_res, message_id)
                    print(f"DEBUG: perform_retrieval done, got {len(documents)} documents")

                    print(f"DEBUG: Calling generate_planned_answers...")
                    serialized_answer_res = MessageHandler.generate_planned_answers(history, documents, eval_res)
                    print(f"DEBUG: generate_planned_answers done")

                print(f"DEBUG: Calling generate_final_response...")
                MessageHandler.generate_final_response(history, documents, serialized_answer_res, message_id)
                print(f"DEBUG: generate_final_response done")

                # Store thinking duration after processing is complete
                SessionManager.finalize_message_with_thinking_duration(message_id)

                # Only ACK after successful processing
                await message.ack()
                print(f"DEBUG: Message ACK'd successfully for session: {body['session_uid']}")

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
                        message_id = message_ref.data[0]["id"]
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
                    # Get channel from message to republish
                    channel = message.channel
                    
                    # Update retry count in body
                    body['__retry_count'] = retry_count + 1
                    
                    # Publish new message with retry count
                    await channel.default_exchange.publish(
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
