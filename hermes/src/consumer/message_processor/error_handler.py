import traceback
from src.common.supabase_client import client as supabase

class ErrorHandler:
    @staticmethod
    def handle_error(e: Exception, message_ref):
        error_msg = f"Error processing message: {str(e)}"
        print(error_msg)
        print(f"Full traceback: {traceback.format_exc()}")

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
                        "content": "Terjadi isu saat menjawab pertanyaan anda, silakan coba ajukan pertanyaan anda kembali🙏",
                        "state": "error",
                    }).eq("id", message_id).execute()
                else:
                    print("Could not extract message_id from message_ref for error update")
            except Exception as db_error:
                print(f"Failed to update error state in database: {str(db_error)}")
        
        return {"status": "Error processing message", "error": str(e)}
