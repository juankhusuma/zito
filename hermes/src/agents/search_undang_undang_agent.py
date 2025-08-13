import time
import json
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import SEARCH_UNDANG_UNDANG_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.undang_undang_search import undang_undang_document_search, search_dense_undang_undang_documents

def evaluate_es_query(query: dict):
    try:
        documents = undang_undang_document_search(query=query)
        return (documents, None)
    except Exception as e:
        print(f"Error searching legal documents: {str(e)}")
        return (None, str(e))

def generate_and_execute_es_query_undang_undang(questions: list[str]):
    time.sleep(1)
    last_no_hit = False
    prev_query = None
    max_attempt = 3
    while True and max_attempt > 0:
        max_attempt -= 1
        es_query_res = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[{
                "role": "user",
                "parts": [
                    {
                        "text": "\n".join(["- " + question for question in questions])
                    }
                ],
            }],
            config=types.GenerateContentConfig(
                candidate_count=1,
                temperature=0.2,
                system_instruction=SEARCH_UNDANG_UNDANG_AGENT_PROMPT + "\n".join(["- " + question for question in questions]) + \
                "" if not last_no_hit else REWRITE_PROMPT(prev_query),
                response_mime_type="application/json",
            ),
        )
        query_json = None
        cleaned_text = es_query_res.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace("```", "").strip()
        try:
            query_json = json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("Error decoding JSON response from Gemini")
            continue
        documents, error = evaluate_es_query(query_json)
        dense_documents = [
            search_dense_undang_undang_documents(
                query=question, top_k=5
            ) for question in questions
        ]
        result = []
        for doc in dense_documents:
            result.extend(doc.get("matches", []))

        dense_documents = result
        for doc in dense_documents:
            del doc["values"]
            doc["metadata"]["_type"] = "undang-undang"
            
        if len(documents) == 0:
            last_no_hit = True
            continue
        if error is None:
            return documents, dense_documents
        
        time.sleep(1)
