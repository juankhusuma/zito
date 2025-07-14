from datetime import datetime
from src.common.supabase_client import client as supabase
from ...agents.title_agent import generate_title
from ...model.search import History
from .agent_caller import AgentCaller

class SessionManager:
    @staticmethod
    def init_message(session_uid: str, user_uid: str):
        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", session_uid).execute()
        message_ref = (
            supabase.table("chat")
            .insert({
                "role": "assistant",
                "content": "",
                "session_uid": session_uid,
                "user_uid": user_uid,
                "state": "loading",
            })
            .execute()
        )
        return message_ref

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
        except Exception as e:
            print(f"Failed to generate title: {str(e)}")
