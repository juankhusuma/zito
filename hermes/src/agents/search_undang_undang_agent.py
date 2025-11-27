import time
from src.utils.logger import HermesLogger

import json
from concurrent.futures import ThreadPoolExecutor
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import SEARCH_UNDANG_UNDANG_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.undang_undang_search import undang_undang_document_search, search_dense_undang_undang_documents
from src.utils.embedding_helper import batch_embed_queries

logger = HermesLogger("uu_agent")

def evaluate_es_query(query: dict):
    try:
        documents = undang_undang_document_search(query=query)
        return (documents, None)
    except Exception as e:
        logger.error("Search failed", error=str(e))
        return (None, str(e))

def generate_and_execute_es_query_undang_undang(questions: list[str]):
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

        # Pinecone dense search with batch embedding optimization
        try:
            start_time = time.time()

            # Batch generate embeddings for all questions at once
            embeddings = batch_embed_queries(questions)
            logger.debug("Batch embedding complete", queries=len(questions))

            # Parallel Pinecone queries with pre-computed embeddings
            max_workers = min(len(questions), 5)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(search_dense_undang_undang_documents, embeddings[i], 5)
                    for i in range(len(questions))
                ]
                dense_results = [future.result() for future in futures]

            # Flatten results
            result = []
            for doc in dense_results:
                result.extend(doc.get("matches", []))
            dense_documents = result

            # Clean up metadata
            for doc in dense_documents:
                del doc["values"]
                doc["metadata"]["_type"] = "undang-undang"

            elapsed = time.time() - start_time
            logger.debug("Pinecone search complete", questions=len(questions), documents=len(dense_documents), duration_ms=int(elapsed*1000))
        except Exception as e:
            logger.warning("Pinecone search failed", error=str(e))
            dense_documents = []

        if len(documents) == 0:
            continue
        if error is None:
            return documents, dense_documents

        time.sleep(1)
    return [], []