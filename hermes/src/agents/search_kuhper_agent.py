import time
import json
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import SEARCH_KUHPER_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.kuhper_search import kuhper_document_search, search_dense_kuhper_documents

def evaluate_es_query(query: dict):
    try:
        documents = kuhper_document_search(query=query)
        return (documents, None)
    except Exception as e:
        print(f"Error searching legal documents: {str(e)}")
        return (None, str(e))

def generate_and_execute_es_query_kuhper(questions: list[str]):
    time.sleep(1)
    max_attempt = 3
    while True and max_attempt > 0:
        max_attempt -= 1
        query_json = {}
        query_json["query"] = {
            "bool": {
                "should": [
                    {"match": {"content": question}} for question in questions
                ]
            }
        }
        documents, error = evaluate_es_query(query_json)

        # Pinecone dense search - now enabled with proxy support
        try:
            print(f"DEBUG: Calling Pinecone dense search for {len(questions)} questions...")
            dense_documents = [
                search_dense_kuhper_documents(
                    query=question, top_k=5
                ) for question in questions
            ]
            result = []
            for doc in dense_documents:
                result.extend(doc.get("matches", []))
            dense_documents = result
            for doc in dense_documents:
                del doc["values"]
                doc["metadata"]["_type"] = "kuhper"
            print(f"DEBUG: Pinecone dense search returned {len(dense_documents)} documents")
        except Exception as e:
            print(f"WARNING: Pinecone dense search failed: {e}")
            print(f"WARNING: Falling back to ES-only mode")
            dense_documents = []

        if len(documents) == 0:
            continue
        if error is None:
            return documents, dense_documents
        
        time.sleep(1)
    return [], []