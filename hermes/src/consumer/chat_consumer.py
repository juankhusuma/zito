from pydantic import BaseModel
import aio_pika
from src.common.gemini_client import client as gemini_client
from src.common.supabase_client import client as supabase
from dotenv import load_dotenv
import os, io
from google.genai import types
from ..config.llm import CHATBOT_SYSTEM_PROMPT, MODEL_NAME, CHECK_SYSTEM_PROMPT, EXTRACT_SYSTEM_PROMPT
from ..tools.search_legal_document import legal_document_search
from datetime import datetime
load_dotenv()
import httpx
import json
import re
from pydantic import BaseModel
import asyncio

class CheckMessage(BaseModel):
    need_retrieval: bool
    queries: list[str]

class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: str

class History(BaseModel):
    messages: list[ChatMessage]
    session_uid: str
    user_uid: str
    access_token: str
    refresh_token: str

class ChatConsumer:
    @staticmethod
    async def consume(loop):
        conn =  await aio_pika.connect_robust(
            host=os.getenv("RABBITMQ_HOST", "localhost"), loop=loop, login=os.getenv("RABBITMQ_USER"), password=os.getenv("RABBITMQ_PASS"),
        )
        channel = await conn.channel()
        queue = await channel.declare_queue("chat")
        await queue.consume(ChatConsumer.process_message, no_ack=False)
        return conn
    
    @staticmethod
    def __serialize_message(messages: History):
        history = []
        for msg in messages:
            history.append(
                {
                    "role": msg["role"] if msg["role"] != "assistant" else "model",
                    "parts": [
                        {
                            "text": msg["content"],
                        }
                    ],
                }
            )
        return history

    @staticmethod
    async def process_message(message):
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        history = ChatConsumer.__serialize_message(body["messages"])
        is_new = len(history) == 1
        msg = ""
        supabase.auth.set_session(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
        )

        supabase.table("session").update({
            "last_updated_at": datetime.now().isoformat(),
        }).eq("id", body["session_uid"]).execute()

        message_ref = supabase.table("chat").insert({
            "role": "assistant",
            "content": "",
            "session_uid": body["session_uid"],
            "user_uid": body["user_uid"],
            "state": "loading",
        }).execute()

        res = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=CHECK_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=CheckMessage
            ),
        )
        check_need_retrieval = CheckMessage(**json.loads(
            res.candidates[0].content.parts[0].text
        ))
        print(check_need_retrieval)
        
        files = []
        if check_need_retrieval.need_retrieval and len(check_need_retrieval.queries) > 0:
            supabase.table("chat").update({
                "state": "searching",
            }).eq("id", message_ref.data[0]["id"]).execute()
            print(f"Retrieval needed for queries: {check_need_retrieval.queries}")
            # Process all queries in parallel
            files = await ChatConsumer.__process_queries_in_parallel(check_need_retrieval.queries[:3])
            print(f"Retrieved {len(files)} files for context enrichment")
            print(files)
        
        context = ""
        if len(files) > 0:
            res = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=files + history,
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACT_SYSTEM_PROMPT,
                ),
            )
            context = res.candidates[0].content.parts[0].text
            supabase.table("chat").update({
                "context": context,
                "state": "extracting",
            }).eq("id", message_ref.data[0]["id"]).execute()

        if context != "":
            print(f"Context extracted: {context}")
            user_prompt = history.pop()
            history.extend([{
                "role": "model",
                "parts": [
                    {
                        "text": context,
                    }
                ],
            }, user_prompt])

        res = gemini_client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
            ),
        )

        msg = ""
        for i, chunk in enumerate(res):
            msg += "".join([part.text for part in chunk.candidates[0].content.parts])
            if i % 2 == 0:
                supabase.table("chat").update({
                    "content": msg,
                    "state": "generating"
                    }).eq("id", message_ref.data[0]["id"]).execute()

        supabase.table("chat").update({
            "content": msg,
            "state": "done",
        }).eq("id", message_ref.data[0]["id"]).execute()

        if is_new:
            res = gemini_client.models.generate_content_stream(
                model="gemini-2.0-flash-lite",
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction="""
                    A title for the chat session, given the context of the chat, 
                    just a sentence with a few words will do.
                    Focus on the content of the chat, and make it as short as possible.
                    Instead of "Pembahasan isi UU No. 1 Tahun 2021", you can just say "UU No. 1 Tahun 2021: Pembahasan"
                    """,
                    max_output_tokens=500,
                ),
            )
            title = ""
            for chunk in res:
                title += "".join([part.text for part in chunk.candidates[0].content.parts])
            supabase.table("session").update({
                "title": title.replace("*", "").replace("#", "").replace("`", ""),
            }).eq("id", body["session_uid"]).execute()
            print(f"Chat session title: {title}")

        return {"status": "Message sent successfully"}

    @staticmethod
    async def __process_queries_in_parallel(queries: list[str]) -> list[types.File]:
        """Process all retrieval queries in parallel to get relevant documents"""
        # from src.common.ollama_client import infer
        # from src.common.pinecone_client import index
        import httpx
        import asyncio
        
        print("Starting parallel document retrieval process...")
        
        # Step 1: Generate embeddings for all queries in parallel
        # async def embed_query(query: str):
        #     try:
        #         embedding = infer.embed(input=query, model="bge-m3").embeddings[0]
        #         return {"query": query, "embedding": embedding}
        #     except Exception as e:
        #         print(f"Error embedding query '{query}': {str(e)}")
        #         return {"query": query, "embedding": None}
        
        # embed_tasks = [embed_query(query) for query in queries]
        # embeddings_results = await asyncio.gather(*embed_tasks)
        # valid_embeddings = [r for r in embeddings_results if r["embedding"] is not None]
        
        # Step 2: Query vector DB and perform sparse search in parallel
        document_ids = set()
        
        # Vector search function
        # async def vector_search(query_data):
        #     try:
        #         query, embedding = query_data["query"], query_data["embedding"]
        #         if embedding is None:
        #             return []
                
        #         results = index.query(
        #             vector=embedding,
        #             top_k=3,
        #             include_metadata=True
        #         )
        #         doc_ids = [match['id'] for match in results['matches']]
        #         print(f"Vector search for '{query}' returned: {doc_ids}")
        #         return doc_ids
        #     except Exception as e:
        #         print(f"Error in vector search for '{query_data['query']}': {str(e)}")
        #         return []
        
        # Sparse search function
        async def sparse_search(query: str):
            try:
                from sqlalchemy import text
                from ..common.postgres import db
                
                # Execute SQL query directly for sparse search
                sparse_results = db.execute(
                    text("""--sql
                    SELECT DISTINCT chunk.document_id,
                    ts_rank_cd(chunk.full_text_search, plainto_tsquery('indonesian', :query)) AS rank
                    FROM legal_document_pages AS chunk
                    WHERE chunk.full_text_search @@ plainto_tsquery('indonesian', :query)
                    ORDER BY rank DESC
                    LIMIT 3;
                    """), parameters={"query": query}
                ).fetchall()
                
                doc_ids = [result[0] for result in sparse_results]
                print(f"Sparse search for '{query}' returned: {doc_ids}")
                return doc_ids
            except Exception as e:
                print(f"Error in sparse search for '{query}': {str(e)}")
                return []
        
        # Run all searches in parallel
        # vector_tasks = [vector_search(embedding) for embedding in valid_embeddings]
        sparse_tasks = [sparse_search(query) for query in queries]
        
        # all_search_tasks = vector_tasks + sparse_tasks
        all_search_tasks = sparse_tasks
        all_search_results = await asyncio.gather(*all_search_tasks)
        
        # Combine and dedupe results
        for result_list in all_search_results:
            for doc_id in result_list:
                document_ids.add(doc_id)
        
        print(f"Combined search returned {len(document_ids)} unique documents")
        
        # Step 3: Get metadata and extract references
        async def get_document_metadata(doc_id: str):
            try:
                from sqlalchemy import text
                from ..common.postgres import db
                
                metadata = db.execute(
                    text("""--sql
                    SELECT mengubah, diubah_oleh,
                        mencabut, dicabut_oleh, melaksanakan_amanat_peraturan, dilaksanakan_oleh_peraturan_pelaksana
                    FROM legal_documents WHERE id = :id;
                    """), parameters={"id": doc_id}
                ).fetchone()
                
                ref_ids = []
                if metadata:
                    for field in metadata:
                        if not field:
                            continue
                            
                        if isinstance(field, list):
                            for item in field:
                                if isinstance(item, dict) and 'ref' in item:
                                    ref_ids.append(item['ref'])
                        elif isinstance(field, dict) and 'ref' in field:
                            ref_ids.append(field['ref'])
                
                return ref_ids
            except Exception as e:
                print(f"Error getting metadata for document {doc_id}: {str(e)}")
                return []
        
        metadata_tasks = [get_document_metadata(doc_id) for doc_id in document_ids]
        metadata_results = await asyncio.gather(*metadata_tasks)
        
        # Add reference document IDs
        for refs in metadata_results:
            for ref in refs:
                document_ids.add(ref)
        
        print(f"After metadata references, have {len(document_ids)} unique documents")
        document_filenames = [f"{doc_id}.pdf" for doc_id in document_ids]
        
        # Step 4: Download documents in parallel
        existing_files = [f.display_name for f in gemini_client.files.list()]
        
        async def download_and_upload_document(filename: str):
            try:
                # Skip if already in Gemini
                if filename in existing_files:
                    file_obj = next((f for f in gemini_client.files.list() if f.display_name == filename), None)
                    if file_obj:
                        print(f"Using existing file: {filename}")
                        return file_obj
                
                # Try primary source
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://chat.lexin.cs.ui.ac.id/static/doc/{filename}", timeout=10.0)
                    
                    if response.status_code != 200:
                        # Try alternate source
                        doc_id = filename.replace(".pdf", "")
                        alt_response = await client.get(f"https://peraturan.go.id/id/{doc_id}", timeout=10.0)
                        
                        if alt_response.status_code != 200:
                            print(f"Failed to download {filename} from both sources")
                            return None
                            
                        # Extract PDF links from alternate source
                        pattern = re.compile(r"/([^/]+\.pdf)")
                        for pdf_name in re.findall(pattern, alt_response.content.decode("utf-8")):
                            pdf_link = f"https://peraturan.go.id/files/{pdf_name}"
                            pdf_response = await client.get(pdf_link, timeout=10.0)
                            
                            if pdf_response.status_code == 200:
                                content = pdf_response.content
                                break
                        else:
                            print(f"No valid PDFs found for {filename}")
                            return None
                    else:
                        content = response.content
                
                # Check file size
                if len(content) < 100:
                    print(f"Warning: {filename} too small ({len(content)} bytes)")
                    return None
                
                # Upload to Gemini
                doc_io = io.BytesIO(content)
                start_time = datetime.now()
                file = gemini_client.files.upload(
                    file=doc_io,
                    config=types.UploadFileConfig(
                        display_name=filename,
                        mime_type="application/pdf",
                    )
                )
                upload_time = (datetime.now() - start_time).total_seconds()
                print(f"Successfully uploaded {filename} ({len(content)} bytes) in {upload_time:.2f}s")
                return file
                
            except httpx.TimeoutException:
                print(f"Timeout downloading {filename}, skipping")
                return None
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                return None
        
        # Process files in batches to avoid overwhelming the system
        batch_size = 10  # Increased from 5
        all_files = []
        total_start_time = datetime.now()
        
        # Create connection pool for reuse
        async with httpx.AsyncClient(timeout=15.0) as client:
            for i in range(0, len(document_filenames), batch_size):
                batch_start_time = datetime.now()
                batch = document_filenames[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(document_filenames) + batch_size - 1)//batch_size}: {len(batch)} files")
                
                # First try existing files to avoid unnecessary downloads
                existing_batch = [f for f in batch if f in existing_files]
                if existing_batch:
                    print(f"Found {len(existing_batch)} already uploaded files in batch")
                    for filename in existing_batch:
                        file_obj = next((f for f in gemini_client.files.list() if f.display_name == filename), None)
                        if file_obj:
                            all_files.append(file_obj)
                            batch.remove(filename)
                
                if batch:  # Only process remaining files that need downloading
                    batch_tasks = [download_and_upload_document(filename) for filename in batch]
                    batch_results = await asyncio.gather(*batch_tasks)
                    valid_files = [f for f in batch_results if f is not None]
                    all_files.extend(valid_files)
                
                batch_time = (datetime.now() - batch_start_time).total_seconds()
                print(f"Batch processed in {batch_time:.2f}s, valid files so far: {len(all_files)}/{len(document_filenames)}")
        
        total_time = (datetime.now() - total_start_time).total_seconds()
        print(f"Document processing complete: {len(all_files)}/{len(document_filenames)} files in {total_time:.2f}s")
        return all_files


