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
from src.utils.logger import HermesLogger

logger = HermesLogger("answer")

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
    logger.debug("Planned answer generated", answer_count=len(serialized_answer_res.answers))
    return serialized_answer_res

def stream_answer_user(context: History, message_id: str, documents: list[dict], serialized_answer_res: QnAList):
    """Stream the response and update the database with debounced updates"""
    full_content = ""
    citation_processor = CitationProcessor()

    chunk_count = 0
    chunks_per_update = 3
    last_update_time = time.time()
    update_interval_seconds = 0.2
    thinking_duration_sent = False
    thinking_start_time = None

    try:
        msg_res = supabase.table("chat").select("thinking_start_time").eq("id", message_id).single().execute()
        if msg_res.data and msg_res.data.get("thinking_start_time"):
            start_time_str = msg_res.data.get("thinking_start_time")
            start_time_str = start_time_str.replace('Z', '+00:00')
            thinking_start_time = datetime.fromisoformat(start_time_str)
            logger.info("Thinking start time retrieved", start_time=start_time_str, message_id=message_id)
    except Exception as e:
        logger.warning("Failed to get thinking start time", error=str(e))

    try:
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

        for chunk in stream:
            if chunk.text:
                if thinking_start_time is not None and not thinking_duration_sent:
                    now = datetime.now(timezone.utc)
                    thinking_duration_ms = int((now - thinking_start_time).total_seconds() * 1000)
                    logger.info(
                        "FIRST CHUNK ARRIVED - Calculating thinking duration",
                        message_id=message_id,
                        start_time=thinking_start_time.isoformat(),
                        end_time=now.isoformat(),
                        duration_ms=thinking_duration_ms,
                        duration_seconds=f"{thinking_duration_ms / 1000:.2f}s"
                    )
                    try:
                        supabase.table("chat").update({
                            "thinking_duration": thinking_duration_ms
                        }).eq("id", message_id).execute()
                        thinking_duration_sent = True
                        logger.info(
                            "Thinking duration SENT to database",
                            message_id=message_id,
                            duration_ms=thinking_duration_ms,
                            duration_display=f"{thinking_duration_ms / 1000:.2f}s"
                        )
                    except Exception as e:
                        logger.error("Failed to update thinking duration", error=str(e), message_id=message_id)

                full_content += chunk.text
                chunk_count += 1
                current_time = time.time()
                time_since_last_update = current_time - last_update_time

                should_update = (chunk_count >= chunks_per_update) or (time_since_last_update >= update_interval_seconds)

                if should_update:
                    try:
                        processed = citation_processor.process(full_content, documents)
                        cleaned_content = processed["content"]
                        references = processed.get("references", [])

                        update_payload = {
                            "content": cleaned_content,
                            "state": "streaming",
                            "citations": references if references else None,
                        }

                        supabase.table("chat").update(update_payload).eq("id", message_id).execute()

                        chunk_count = 0
                        last_update_time = current_time

                    except Exception as db_error:
                        logger.error("Failed to update streaming content", error=str(db_error))
                        continue

        # Final update with complete state
        try:
            processed = citation_processor.process(full_content, documents)
            final_content = processed["content"]
            references = processed.get("references", [])

            try:
                total_citations = len(citation_processor.extract_citations(full_content, documents))
            except Exception:
                total_citations = -1

            referenced_doc_ids = [ref.get("doc_id") for ref in references if isinstance(ref, dict)]
            unique_referenced_doc_ids = sorted({doc_id for doc_id in referenced_doc_ids if doc_id})

            citation_logger = HermesLogger("citation")
            citation_logger.info(
                "Citation processing complete",
                total_citations=total_citations,
                valid_references=len(references),
                doc_ids=",".join(unique_referenced_doc_ids) if unique_referenced_doc_ids else "none"
            )

        except Exception as process_error:
            citation_logger = HermesLogger("citation")
            citation_logger.error("Citation processing failed", error=str(process_error))
            final_content = full_content
            references = []

        supabase.table("chat").update({
            "content": final_content,
            "state": "done",
            "documents": json.dumps(documents, indent=2) if documents else "[]",
            "citations": references if references else None,
        }).eq("id", message_id).execute()
        
        # Create a mock response object for compatibility
        class MockResponse:
            def __init__(self, text):
                self.text = text
        
        return MockResponse(full_content)

    except Exception as e:
        logger.error("Streaming failed, falling back to regular generation", error=str(e))
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

    logger.debug("Fetching metadata", count=len(need_fetch_metadata))

    # Use streaming generation
    if message_id:
        id_to_fetch = []
        for doc in need_fetch_metadata:
            if doc["_index"] == "kuhper": doc["_id"] = "KUH_Perdata"
            if doc["_index"] == "kuhp": doc["_id"] = "UU_1_2023"
            if doc["_id"] not in id_to_fetch:
                id_to_fetch.append(doc["_id"])

        metadata = get_documents_metadata_batch(id_to_fetch)
        logger.debug("Metadata batch fetched", count=len(metadata))

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

        metadata = get_documents_metadata_batch(id_to_fetch)
        logger.debug("Metadata batch fetched", count=len(metadata))

        # Update the database with the final content
        supabase.table("chat").update({
            "content": res.text,
            "state": "done",
            "documents": json.dumps(documents + metadata, indent=2) if documents else "[]",
        }).eq("id", message_id).execute()
        return res