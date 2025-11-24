import time
import json
from datetime import datetime, timezone
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import MODEL_NAME, CHATBOT_SYSTEM_PROMPT, ANSWERING_AGENT_PROMPT
from ..model.search import History, QnAList, Questions
from src.tools.retrieve_document_metadata import get_document_metadata, get_documents_metadata_batch
from src.common.supabase_client import client as supabase
from src.utils.citation_processor import CitationProcessor

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
    citation_processor = CitationProcessor()
    
    # Calculate thinking duration once before streaming starts
    thinking_duration = None
    try:
        msg_res = supabase.table("chat").select("thinking_start_time").eq("id", message_id).single().execute()
        if msg_res.data and msg_res.data.get("thinking_start_time"):
            start_time_str = msg_res.data.get("thinking_start_time")
            # Handle ISO format with Z or offset
            start_time_str = start_time_str.replace('Z', '+00:00')
            start_time = datetime.fromisoformat(start_time_str)
            now = datetime.now(timezone.utc)
            thinking_duration = (now - start_time).total_seconds()
    except Exception as e:
        print(f"Error calculating thinking duration: {e}")

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
                stop_sequences=["Referensi", "Daftar Pustaka", "Sumber:"],
            ),
        )
        
        # Process each chunk and update database
        for chunk in stream:
            if chunk.text:
                full_content += chunk.text
                # Update database with current content
                try:
                    update_payload = {
                        "content": full_content,
                        "state": "streaming",
                    }
                    # Only update thinking_duration if we calculated it
                    if thinking_duration is not None:
                        update_payload["thinking_duration"] = int(thinking_duration * 1000)
                        
                    supabase.table("chat").update(update_payload).eq("id", message_id).execute()
                except Exception as db_error:
                    print(f"Error updating streaming content: {str(db_error)}")
                    continue
        
        # Final post-processing: clean citations & build reference list
        try:
            print("[Citation] Starting citation post-processing...")
            processed = citation_processor.process(full_content, documents)
            final_content = processed["content"]
            references = processed.get("references", [])

            # Lightweight observability for citations in production logs
            try:
                total_citations = len(citation_processor.extract_citations(full_content, documents))
            except Exception:
                total_citations = -1

            referenced_doc_ids = [ref.get("doc_id") for ref in references if isinstance(ref, dict)]
            unique_referenced_doc_ids = sorted({doc_id for doc_id in referenced_doc_ids if doc_id})

            print(
                "[Citation] Processed answer:",
                f"total_citations_in_text={total_citations}",
                f"references_count={len(references)}",
                f"referenced_doc_ids={unique_referenced_doc_ids}",
            )

        except Exception as process_error:
            # If anything goes wrong in citation processing, fall back to raw content
            print(f"[Citation] Citation processing error: {str(process_error)}")
            final_content = full_content
            references = []

        # Final update with complete, cleaned content and canonical citations
        print("[Citation] Final canonical citations:", json.dumps(references, ensure_ascii=False))
        supabase.table("chat").update({
            "content": final_content,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
            # Store canonical citations list into the new JSONB column
            "citations": references if references else None,
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
        
        # Update with final content (no post-processing in fallback path)
        supabase.table("chat").update({
            "content": response.text,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
            # No citation post-processing in this fallback path
            "citations": None,
        }).eq("id", message_id).execute()
        
        return response

def answer_user(history: History, documents: list[dict], serialized_answer_res: QnAList, message_id: str = None):
    time.sleep(1)
    need_fetch_metadata = []
    for doc in documents:
        if doc.get("values") is not None:
            del doc["values"]
        if doc.get("_id") is not None:
            need_fetch_metadata.append({
                "_id": doc["_id"],
                "_index": doc["_index"],
            })
            if "___" in doc["_id"]:
                doc["pasal"] = doc["_id"].split("___")[1]
                doc["_id"] = doc["_id"].split("___")[0]
            if doc["_index"] == "undang-undang":
                doc["_id"] = doc['_id'].replace('Nomor_', '').replace('Tahun_', '').replace('.pdf', '')
            if doc["_index"] == "kuhper":
                doc["_id"] = "KUH_Perdata"
            if doc["_index"] == "kuhp":
                doc["_id"] = "UU_1_2023"    
        if doc.get("id") is not None:
            print(doc)
            if "___" in doc["id"]:
                doc["pasal"] = doc["id"].split("___")[1]
                doc["id"] = doc["id"].split("___")[0]
                doc["id"] = doc['id'].replace('Nomor_', '').replace('Tahun_', '').replace(".pdf", "")
                need_fetch_metadata.append({
                    "_id": doc["id"],
                    "_index": "undang-undang",
                })
            elif doc.get("source") is not None and doc["source"].get("buku_id") is not None:
                doc["id"] = "KUH_Perdata"
                need_fetch_metadata.append({
                    "_id": "KUH_Perdata",
                    "_index": "kuhper",
                })
            else:
                # Keep original ID for all other documents (Perpres, PP, etc.)
                # Only add to metadata fetch list if it looks like a valid document ID
                original_id = doc["id"]
                if original_id and isinstance(original_id, str) and len(original_id) > 0:
                    need_fetch_metadata.append({
                        "_id": original_id,
                        "_index": "peraturan_indonesia",  # Metadata is in peraturan_indonesia index
                    })
                # Note: DO NOT override doc["id"] here - keep the original ID!

    print(f"Need to fetch metadata for: {need_fetch_metadata} $$$$$$$$$$$$$$$")

    # Use streaming generation
    if message_id:
        id_to_fetch = []
        for doc in need_fetch_metadata:
            if doc["_index"] == "kuhper": doc["_id"] = "KUH_Perdata"
            if doc["_index"] == "kuhp": doc["_id"] = "UU_1_2023"
            if doc["_id"] not in id_to_fetch:
                id_to_fetch.append(doc["_id"])

        print(id_to_fetch)
        
        metadata = get_documents_metadata_batch(id_to_fetch)
        print("@@@@@@@@@@@DOC METADATA BATCH", len(metadata))
        
        return stream_answer_user(history, message_id, documents + metadata, serialized_answer_res)
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
                stop_sequences=["Referensi", "Daftar Pustaka", "Sumber:"],
            ),
        )

        id_to_fetch = []
        for doc in need_fetch_metadata:
            if doc["_index"] == "kuhper": doc["_id"] = "KUH_Perdata"
            if doc["_index"] == "kuhp": doc["_id"] = "UU_1_2023"
            if doc["_id"] not in id_to_fetch:
                id_to_fetch.append(doc["_id"])

        print(id_to_fetch)
        
        metadata = get_documents_metadata_batch(id_to_fetch)
        print("@@@@@@@@@@@DOC METADATA BATCH", len(metadata))

        print(metadata)
        
        # Update the database with the final content
        supabase.table("chat").update({
            "content": res.text,
            "state": "done",
            "documents": json.dumps(documents + metadata, indent=2) if documents else "[]",
        }).eq("id", message_id).execute()
        return res