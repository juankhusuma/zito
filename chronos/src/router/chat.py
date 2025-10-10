from fastapi import APIRouter
from ..producer.chat_producer import ChatProducer, History
from ..common.supabase_client import client as supabase
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat")
async def chat_producer(message: History):
    try:
        # Update session last_updated_at
        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", message.session_uid).execute()

        # Create assistant message BEFORE publishing to RabbitMQ
        # This ensures frontend subscription catches the INSERT event
        backend_thinking_start = datetime.now(timezone.utc).isoformat()
        logger.info(f"DEBUG: Creating assistant message for session {message.session_uid}")
        logger.info(f"DEBUG: Setting thinking_start_time to: {backend_thinking_start}")

        chat_data = {
            "role": "assistant",
            "content": "",
            "session_uid": message.session_uid,
            "user_uid": message.user_uid,
            "state": "loading",
            "thinking_start_time": backend_thinking_start,
        }

        logger.info(f"DEBUG: Chat data to insert: {chat_data}")

        message_ref = (
            supabase.table("chat")
            .insert(chat_data)
            .execute()
        )

        message_id = message_ref.data[0]["id"]
        logger.info(f"DEBUG: Assistant message created with id: {message_id}")

        # Now publish to RabbitMQ with message_id
        status = await ChatProducer.publish(message, message_id)
        return status

    except Exception as e:
        logger.error(f"ERROR: Failed to create assistant message or publish: {e}")
        return {"status": "Error", "message": str(e)}