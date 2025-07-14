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
                supabase.table("chat").update({
                    "content": "Terjadi isu saat menjawab pertanyaan anda, silakan coba ajukan pertanyaan anda kembali🙏",
                    "state": "error",
                }).eq("id", message_ref.data[0]["id"]).execute()
            except Exception as db_error:
                print(f"Failed to update error state in database: {str(db_error)}")
        
        return {"status": "Error processing message", "error": str(e)}
