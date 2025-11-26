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
            # Get thinking_start_time from database
            chat_record = supabase.table("chat").select("thinking_start_time").eq("id", message_id).execute()

            if chat_record.data and len(chat_record.data) > 0:
                thinking_start_time = chat_record.data[0].get("thinking_start_time")

                if thinking_start_time:
                    # Parse start time and calculate duration
                    from dateutil.parser import parse as parse_date
                    start_time = parse_date(thinking_start_time)
                    end_time = datetime.now(timezone.utc)

                    # Ensure both datetimes are timezone-aware
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)

                    # Calculate duration in milliseconds
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)

                    # Update chat with thinking duration
                    supabase.table("chat").update({
                        "thinking_duration": duration_ms
                    }).eq("id", message_id).execute()

                    print(f"Stored thinking duration: {duration_ms}ms for message {message_id}")
                else:
                    print(f"No thinking_start_time found for message {message_id}")
            else:
                print(f"Chat record not found for message {message_id}")

        except Exception as e:
            print(f"Failed to store thinking duration: {str(e)}")
