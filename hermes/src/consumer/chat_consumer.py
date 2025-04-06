from pydantic import BaseModel
import aio_pika
from src.common.gemini_client import client as gemini_client
from src.common.supabase_client import get_client
from dotenv import load_dotenv
import os, io
from google.genai import types
from ..config.llm import CHATBOT_SYSTEM_PROMPT, SEARCH_SYSTEM_PROMPT, MODEL_NAME
from ..tools.search_legal_document import legal_document_search
load_dotenv()
import httpx
import json
import re

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
    def __download_from_external_source(doc_id: str) -> list[types.File]:
        response = httpx.get(f"https://peraturan.go.id/id/{doc_id}")
        print(f"https://peraturan.go.id/id/{doc_id}")

        if response.status_code != 200:
            print(f"Error downloading {doc_id}: HTTP {response.status_code}")
            return []
        
        content = response.content
        # find pattern /{anything here}.pdf
        pattern = re.compile(r"/([^/]+\.pdf)")
        files_in_html = []
        for filename in re.findall(pattern, content.decode("utf-8")):
            print(f"Found PDF link: {filename}")
            files_in_html.append(filename)
        
        # there could be multiple matches, so we need to iterate over them
        for pdf_link in files_in_html:
            if pdf_link.startswith("/"):
                pdf_link = pdf_link[1:]
            pdf_link = f"https://peraturan.go.id/files/{pdf_link}"
            response = httpx.get(pdf_link)
            if response.status_code != 200:
                print(f"Error downloading {pdf_link}: HTTP {response.status_code}")
                continue
            content = response.content
            doc_io = io.BytesIO(content)
            gemini_client.files.upload(
                file=doc_io,
                config=types.UploadFileConfig(
                    display_name=pdf_link.split("/")[-1],
                    mime_type="application/pdf",
                )
            )
            files_in_html.append(pdf_link.split("/")[-1])
        return files_in_html


    
    @staticmethod
    def __handle_document_context(search: str) -> list[types.File]:
        file_names = legal_document_search(search)
        unique_file_names = list(set(file_names))
        print(f"Found documents: {unique_file_names}")
        files = []
        existing_files = [f.display_name for f in gemini_client.files.list()]
        
        for file_name in unique_file_names:
            try:
                # Check if file already exists in Gemini
                if file_name in existing_files:
                    file_obj = next((f for f in gemini_client.files.list() if f.display_name == file_name), None)
                    if file_obj:
                        print(f"Using existing file: {file_name}")
                        files.append(file_obj)
                        continue
                
                # Download file
                response = httpx.get(f"https://chat.lexin.cs.ui.ac.id/static/doc/{file_name}")
                if response.status_code != 200:
                    print(f"Error downloading {file_name}: HTTP {response.status_code}")
                    # Check if the file is from an external source
                    files = ChatConsumer.__download_from_external_source(file_name.replace(".pdf", ""))
                    if not files:
                        print(f"Error downloading {file_name} from external source")
                        continue
                    else:
                        print(f"Downloaded {file_name} from external source")
                        files.append(file_name)
                        continue
                    
                content = response.content
                # Check if file has content
                if len(content) < 100:  # Simple check for minimum viable PDF size
                    print(f"Warning: {file_name} appears to be too small ({len(content)} bytes), skipping")
                    continue
                    
                doc_io = io.BytesIO(content)
                
                # Upload to Gemini
                print(f"Uploading new file: {file_name} ({len(content)} bytes)")
                file = gemini_client.files.upload(
                    file=doc_io,
                    config=types.UploadFileConfig(
                        display_name=file_name,
                        mime_type="application/pdf",
                    )
                )
                files.append(file)
                print(f"Successfully uploaded: {file_name}")
                
            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")
                # Continue with other files instead of failing completely
                continue
                
        print(f"Total valid files ready for processing: {len(files)}")
        return files

    @staticmethod
    async def process_message(message):
        await message.ack()
        body = json.loads(message.body.decode("utf-8"))
        history = ChatConsumer.__serialize_message(body["messages"])

        supabase = await get_client()
        msg = ""
        await supabase.auth.set_session(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
        )
        message_ref = await supabase.table("chat").insert({
            "role": "assistant",
            "content": "",
            "session_uid": body["session_uid"],
            "user_uid": body["user_uid"],
        }).execute()
    
        # try:
        files = ChatConsumer.__handle_document_context("\n".join([m["parts"][0]["text"] for m in history[-5:] if m["role"] == "user"])) 
        await supabase.table("chat").update({
            "is_loading": False,
        }).eq("id", message_ref.data[0]["id"]).execute()

        
        res = gemini_client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=(*files, *history),
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
            ),
        )
        
        for chunk in res:
            msg += "".join([part.text for part in chunk.candidates[0].content.parts])
            res = await supabase.table("chat").update({"content": msg}).eq("id", message_ref.data[0]["id"]).execute()
        # except Exception as e:
        #     await supabase.table("chat").update({
        #         "has_error": True,
        #         "has_finished": True,
        #     }).eq("id", message_ref.data[0]["id"]).execute()

        await supabase.from_("chat").update({"content": msg}).eq("id", message_ref.data[0]["id"]).execute()
        return {"status": "Message sent successfully"}


