

import time
import json
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import SEARCH_KUHP_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.kuhp_search import kuhp_document_search as legal_document_search, search_dense_kuhp_documents

def evaluate_es_query(query: dict):
    try:
        documents = legal_document_search(query=query)
        return (documents, None)
    except Exception as e:
        print(f"Error searching legal documents: {str(e)}")
        return (None, str(e))

def generate_and_execute_es_query_kuhp(questions: list[str]):
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

        # TEMPORARILY DISABLED: Pinecone dense search (blocked by firewall)
        # TODO: Re-enable when Pinecone is accessible or migrate to local vector DB
        # dense_documents = [
        #     search_dense_kuhp_documents(
        #         query=question, top_k=5
        #     ) for question in questions
        # ]
        # result = []
        # for doc in dense_documents:
        #     result.extend(doc.get("matches", []))
        # dense_documents = result
        # for doc in dense_documents:
        #     del doc["values"]
        #     doc["metadata"]["_type"] = "kuhp"

        # Use empty dense_documents (ES only mode)
        dense_documents = []

        if len(documents) == 0:
            continue
        if error is None:
            return documents, dense_documents
        
        time.sleep(1)
    return [], []