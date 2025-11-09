import time
import json
from concurrent.futures import ThreadPoolExecutor
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import SEARCH_PERPRES_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.perpres_search import perpres_document_search, search_dense_perpres_documents

def evaluate_es_query(query: dict):
    try:
        documents = perpres_document_search(query=query)
        return (documents, None)
    except Exception as e:
        print(f"Error searching perpres documents: {str(e)}")
        return (None, str(e))

def generate_and_execute_es_query_perpres(questions: list[str]):
    max_attempt = 3
    while True and max_attempt > 0:
        max_attempt -= 1
        query_json = {}
        query_json["query"] = {
            "bool": {
                "should": [
                    {"match": {"isi": question}} for question in questions
                ]
            }
        }
        documents, error = evaluate_es_query(query_json)

        # Pinecone dense search - PARALLEL execution for better performance
        try:
            print(f"DEBUG: Calling Pinecone dense search for Perpres - {len(questions)} questions in PARALLEL...")
            start_time = time.time()

            # Use ThreadPoolExecutor to parallelize Pinecone queries
            max_workers = min(len(questions), 5)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all queries in parallel
                futures = [
                    executor.submit(search_dense_perpres_documents, question, 5)
                    for question in questions
                ]
                # Collect results as they complete
                dense_results = [future.result() for future in futures]

            # Flatten results
            result = []
            for dense_result in dense_results:
                for document in dense_result:
                    result.append(document)

            elapsed_time = time.time() - start_time
            print(f"DEBUG: Perpres Pinecone search completed in {elapsed_time:.2f}s (parallel), found {len(result)} dense documents")

        except Exception as e:
            print(f"DEBUG: Perpres Pinecone search failed: {e}")
            result = []

        if documents and error is None:
            return documents, result
        else:
            print(f"Retrying...")
            time.sleep(1)

    print("Max retries reached. Returning empty results.")
    return [], []
