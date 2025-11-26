import time
import json
from concurrent.futures import ThreadPoolExecutor
from src.common.gemini_client import client as gemini_client
from src.utils.logger import HermesLogger
from google.genai import types
from ..config.llm import SEARCH_PERPRES_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.perpres_search import perpres_document_search, search_dense_perpres_documents

logger = HermesLogger("perpres_agent")

def evaluate_es_query(query: dict):
    try:
        documents = perpres_document_search(query=query)
        return (documents, None)
    except Exception as e:
        logger.error("Perpres search failed", error=str(e))
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

        try:
            start_time = time.time()
            max_workers = min(len(questions), 5)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(search_dense_perpres_documents, question, 5)
                    for question in questions
                ]
                dense_results = [future.result() for future in futures]

            result = []
            for dense_result in dense_results:
                for document in dense_result:
                    result.append(document)

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.debug("Pinecone search complete", questions=len(questions), documents=len(result), duration_ms=elapsed_ms)

        except Exception as e:
            logger.warning("Pinecone search failed", error=str(e))
            result = []

        if documents and error is None:
            return documents, result
        else:
            logger.debug("Retrying search", attempt=max_attempt)
            time.sleep(1)

    logger.warning("Max retries reached, returning empty results")
    return [], []
