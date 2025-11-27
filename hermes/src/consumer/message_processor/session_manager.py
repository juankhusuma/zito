from datetime import datetime, timezone
from src.common.supabase_client import client as supabase
from src.utils.logger import HermesLogger
from ...agents.title_agent import generate_title
from ...model.search import History
from .agent_caller import AgentCaller

logger = HermesLogger("session")

class SessionManager:
    @staticmethod
    def init_message(session_uid: str, user_uid: str, thinking_start_time: str = None):
        try:
            supabase.table("session").update({
                "last_updated_at": datetime.now().isoformat(),
            }).eq("id", session_uid).execute()

            backend_thinking_start = datetime.now(timezone.utc).isoformat()

            chat_data = {
                "role": "assistant",
                "content": "",
                "session_uid": session_uid,
                "user_uid": user_uid,
                "state": "loading",
                "thinking_start_time": backend_thinking_start,
            }

            message_ref = (
                supabase.table("chat")
                .insert(chat_data)
                .execute()
            )
            logger.debug("Assistant message created", session_uid=session_uid)
            return message_ref
        except Exception as e:
            logger.error("Failed to create assistant message", error=str(e))
            raise

    @staticmethod
    def handle_new_chat(history: History, session_uid: str):
        try:
            title = AgentCaller.retry_with_exponential_backoff(
                generate_title, max_attempts=2, history=history
            )
            supabase.table("session").update({
                "title": title.replace("*", "").replace("#", "").replace("`", ""),
                "last_updated_at": datetime.now().isoformat(),
            }).eq("id", session_uid).execute()
            logger.debug("Session title generated", session_uid=session_uid)
        except Exception as e:
            logger.warning("Failed to generate title", error=str(e))

    @staticmethod
    def finalize_message_with_thinking_duration(message_id: str):
        """Calculate and store thinking duration when message is completed"""
        try:
            chat_record = supabase.table("chat").select("thinking_start_time, thinking_duration").eq("id", message_id).execute()

            if chat_record.data and len(chat_record.data) > 0:
                existing_duration = chat_record.data[0].get("thinking_duration")

                if existing_duration is not None and existing_duration > 0:
                    logger.info(
                        "FINALIZE: thinking_duration already set, skipping recalculation",
                        message_id=message_id,
                        existing_duration_ms=existing_duration,
                        existing_duration_display=f"{existing_duration / 1000:.2f}s"
                    )
                    return

                thinking_start_time = chat_record.data[0].get("thinking_start_time")

                if thinking_start_time:
                    from dateutil.parser import parse as parse_date
                    start_time = parse_date(thinking_start_time)
                    end_time = datetime.now(timezone.utc)

                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)

                    duration_ms = int((end_time - start_time).total_seconds() * 1000)

                    supabase.table("chat").update({
                        "thinking_duration": duration_ms
                    }).eq("id", message_id).execute()

                    logger.warning(
                        "FINALIZE: thinking_duration was NOT set during streaming, calculating now (fallback)",
                        message_id=message_id,
                        duration_ms=duration_ms,
                        duration_display=f"{duration_ms / 1000:.2f}s"
                    )
                else:
                    logger.warning("No thinking_start_time found", message_id=message_id)
            else:
                logger.warning("Chat record not found", message_id=message_id)

        except Exception as e:
            logger.error("Failed to finalize thinking duration", error=str(e), message_id=message_id)
