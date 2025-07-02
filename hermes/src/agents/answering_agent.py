
import time
import json
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import MODEL_NAME, CHATBOT_SYSTEM_PROMPT, ANSWERING_AGENT_PROMPT
from ..model.search import History, QnAList, Questions
from src.common.supabase_client import client as supabase

def answer_generated_questions(history: History, documents: list[dict], serilized_check_res: Questions):
    time.sleep(1)
    answer_res = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=ANSWERING_AGENT_PROMPT(documents, serilized_check_res.questions),
                response_mime_type="application/json",
                response_schema=QnAList,
                temperature=0.2,
            ),
        )
    serialized_answer_res = QnAList.model_validate(answer_res.parsed)
    print(f"Planned Answer: {serialized_answer_res}")
    return serialized_answer_res

def stream_answer_user(context: History, message_id: str, documents: list[dict], serialized_answer_res: QnAList):
    """Stream the response and update the database in real-time"""
    full_content = ""
    
    try:
        # Generate streaming response
        stream = gemini_client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT + f"""
                Planned Answer:
                {serialized_answer_res.model_dump_json()}

                Retrieved Context:
                {json.dumps(documents, indent=2) if documents else ""}
                """,
            ),
        )
        
        # Process each chunk and update database
        for chunk in stream:
            if chunk.text:
                full_content += chunk.text
                # Update database with current content
                try:
                    supabase.table("chat").update({
                        "content": full_content,
                        "state": "streaming",
                    }).eq("id", message_id).execute()
                except Exception as db_error:
                    print(f"Error updating streaming content: {str(db_error)}")
                    continue
        
        # Final update with complete content
        supabase.table("chat").update({
            "content": full_content,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
        }).eq("id", message_id).execute()
        
        # Create a mock response object for compatibility
        class MockResponse:
            def __init__(self, text):
                self.text = text
        
        return MockResponse(full_content)
        
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        # Fallback to regular generation
        response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
            ),
        )
        
        # Update with final content
        supabase.table("chat").update({
            "content": response.text,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
        }).eq("id", message_id).execute()
        
        return response

def answer_user(history: History, documents: list[dict], serialized_answer_res: QnAList, message_id: str = None):
    time.sleep(1)
    # Use streaming generation
    if message_id:
        return stream_answer_user(history, message_id, documents, serialized_answer_res)
    else:
        res = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT + f"""
                Planned Answer:
                {serialized_answer_res.model_dump_json()}

                Retrieved Context:
                {json.dumps(documents, indent=2) if documents else ""}
                """,
            ),
        )
        # Update the database with the final content
        supabase.table("chat").update({
            "content": res.text,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
        }).eq("id", message_id).execute()
        return res
