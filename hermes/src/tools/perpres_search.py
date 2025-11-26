import os
import json
import time
import requests
from typing import Dict, Any, List
from src.common.gemini_client import client as gemini_client
from src.common.pinecone_client import perpres_index
from src.utils.logger import HermesLogger
from dotenv import load_dotenv
load_dotenv()

logger = HermesLogger("perpres_search")

def perpres_document_search(query: dict) -> List[Dict[str, Any]]:
    logger.debug("Starting Perpres search")

    start_time = time.time()
    result = search_perpres_documents_with_fallback(query)
    elapsed = time.time() - start_time

    if "error" in result:
        logger.error("Search failed", error=result['error'])
        return []

    hits = result.get("hits", [])
    logger.info("Search complete", hits=len(hits), duration_ms=int(elapsed * 1000))
    return hits

def search_perpres_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{os.environ.get('ES_BASE_URL', 'https://chat.lexin.cs.ui.ac.id/elasticsearch')}/perpres/_search"
    logger.debug("Executing Elasticsearch query", url=url)

    headers = {"Content-Type": "application/json"}
    search_query["size"] = search_query.get("size", 10)

    try:
        response = requests.post(
            url=url,
            headers=headers,
            json=search_query,
            auth=("elastic", "password"),
            timeout=30
        )

        if response.status_code != 200:
            error_msg = f"Elasticsearch returned status code {response.status_code}"
            logger.error("Elasticsearch request failed", status_code=response.status_code)
            return {"error": error_msg, "message": "Failed to execute search query."}

        data = response.json()
        formatted_response = {
            "total_hits": data.get("hits", {}).get("total", {}).get("value", 0),
            "max_score": data.get("hits", {}).get("max_score"),
            "hits": []
        }

        for hit in data.get("hits", {}).get("hits", []):
            formatted_hit = {
                "score": hit.get("_score"),
                "id": hit.get("_id"),
                "source": hit.get("_source")
            }
            formatted_response["hits"].append(formatted_hit)

        logger.debug("Elasticsearch query successful", total_hits=formatted_response['total_hits'])
        return formatted_response

    except Exception as e:
        logger.error("Elasticsearch query failed", error=str(e))
        return {"error": str(e)}

def search_perpres_documents_with_fallback(original_query: Dict[str, Any]) -> Dict[str, Any]:
    result = search_perpres_documents(original_query)
    if "error" not in result and result.get("total_hits", 0) > 0:
        return result

    logger.warning("Original query returned no results, trying fallback")
    fallback_query = {
        "query": {
            "multi_match": {
                "query": " ".join(_extract_search_terms(original_query)),
                "fields": ["isi", "penjelasan"]
            }
        },
        "size": original_query.get("size", 10)
    }

    return search_perpres_documents(fallback_query)

def _extract_search_terms(query: Dict[str, Any]) -> List[str]:
    terms = []
    
    def extract_from_dict(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ["query", "match", "match_phrase", "term"]:
                    if isinstance(value, str):
                        terms.append(value)
                    elif isinstance(value, dict):
                        extract_from_dict(value)
                elif isinstance(value, (dict, list)):
                    extract_from_dict(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_from_dict(item)
        elif isinstance(obj, str) and len(obj.strip()) > 2:
            clean_term = obj.strip()
            if not clean_term.lower() in ["dan", "atau", "dengan", "yang", "di", "ke", "dari"]:
                terms.append(clean_term)
    
    extract_from_dict(query)
    return list(set(terms))

def search_dense_perpres_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    logger.debug("Starting Pinecone dense search", k=k)

    try:
        res = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=query
        )
        query_embedding = res.embeddings[0].values

        results = perpres_index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True
        )

        documents = []
        for match in results.get('matches', []):
            documents.append({
                "id": match.get('id'),
                "score": match.get('score'),
                "source": match.get('metadata', {})
            })

        logger.debug("Pinecone search complete", documents=len(documents))
        return documents

    except Exception as e:
        logger.error("Pinecone search failed", error=str(e))
        return []
