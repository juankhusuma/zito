
import os
import json
import time
import requests
from typing import Dict, Any, List
from src.common.gemini_client import client as gemini_client
from src.common.pinecone_client import undang_undang_index
from src.utils.logger import HermesLogger
from dotenv import load_dotenv
load_dotenv()

logger = HermesLogger("uu_search")

def undang_undang_document_search(query: dict) -> List[Dict[str, Any]]:
    start_time = time.time()
    result = search_undang_undang_documents_with_fallback(query)
    elapsed = time.time() - start_time

    if "error" in result:
        logger.error("UU search failed", error=result['error'])
        return []

    hits = result.get("hits", [])
    logger.info("UU search complete", hits=len(hits), duration_ms=int(elapsed * 1000))
    return hits

def search_legal_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    
    url = f"{os.environ.get('ES_BASE_URL', 'https://chat.lexin.cs.ui.ac.id/elasticsearch')}/undang-undang/_search"
    
    headers = {"Content-Type": "application/json"}
    
    # Set defaults
    search_query["size"] = search_query.get("size", 10)

    try:
        # Execute the search using requests directly - don't wrap in another "query" object
        request_body = search_query

        request_start = time.time()

        response = requests.post(
            url=url,
            headers=headers,
            json=request_body,
            auth=("elastic", "password"),
            timeout=30
        )

        request_time = time.time() - request_start

        if response.status_code != 200:
            error_msg = f"Elasticsearch returned status code {response.status_code}: {response.text}"
            logger.error("Elasticsearch request failed", status_code=response.status_code)
            return {
                "error": error_msg,
                "message": "Failed to execute search query. Please check your query syntax."
            }

        data = response.json()

        # Format the response to be more user-friendly
        total_hits = data.get("hits", {}).get("total", {}).get("value", 0)
        max_score = data.get("hits", {}).get("max_score")
        
        formatted_response = {
            "total_hits": total_hits,
            "max_score": max_score,
            "hits": []
        }
        
        # Process hits
        hits_data = data.get("hits", {}).get("hits", [])
        
        for i, hit in enumerate(hits_data):
            formatted_hit = {
                "score": hit.get("_score"),
                "id": hit.get("_id"),
                "source": hit.get("_source", {})
            }
            formatted_response["hits"].append(formatted_hit)
        
        # Include aggregations if present
        if "aggregations" in data:
            formatted_response["aggregations"] = data["aggregations"]

        return formatted_response

    except requests.exceptions.Timeout:
        error_msg = "Elasticsearch request timed out after 30 seconds"
        logger.warning("Elasticsearch timeout")
        return {
            "error": error_msg,
            "message": "Search request timed out. Please try again or refine your query."
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to Elasticsearch: {str(e)}"
        logger.error("Elasticsearch connection failed", error=str(e))
        return {
            "error": error_msg,
            "message": "Unable to connect to search service. Please try again later."
        }
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse Elasticsearch response: {str(e)}"
        logger.error("JSON parsing failed", error=str(e))
        return {
            "error": error_msg,
            "message": "Invalid response from search service."
        }
    except Exception as e:
        error_msg = f"Failed to execute search query: {str(e)}"
        logger.error("Unexpected search error", error=str(e))
        return {
            "error": error_msg,
            "message": "Failed to execute search query. Please check your query syntax."
        }
    
def search_dense_undang_undang_documents(query_or_embedding, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Search Pinecone index using either query string or pre-computed embedding.

    Args:
        query_or_embedding: Either a string query or a list of floats (embedding vector)
        top_k: Number of results to return

    Returns:
        Pinecone query response as dictionary
    """
    if isinstance(query_or_embedding, str):
        embed_res = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=[query_or_embedding]
        )
        embeddings = [float(x) for x in embed_res.embeddings[0].values]
    else:
        embeddings = query_or_embedding

    response = undang_undang_index.query(
        vector=embeddings,
        top_k=top_k,
        include_values=True,
        include_metadata=True
    )
    logger.debug("Pinecone search complete", matches=len(response.matches), top_k=top_k)

    return response.to_dict()

def search_undang_undang_documents_with_fallback(search_query: Dict[str, Any]) -> Dict[str, Any]:
    # Try the original query first
    result = search_legal_documents(search_query)

    # If we got results or there was an error, return as is
    if "error" in result:
        return result

    total_hits = result.get("total_hits", 0)
    logger.debug("Primary search complete", hits=total_hits)

    if total_hits > 0:
        return result

    # Extract the original query for fallback modifications
    original_query = search_query.get("query", {})

    # Fallback 1: If it's a bool query, try with just the "should" clauses and lower minimum_should_match
    fallback_query = {
        "query": {
            "match": {
                "content": " ".join(_extract_search_terms(original_query))
            },
            "size": search_query.get("size", 10),
        }
    }

    # Execute the fallback search
    fallback_result = search_legal_documents(fallback_query)
    if "error" in fallback_result:
        return fallback_result
    fallback_hits = fallback_result.get("total_hits", 0)
    logger.debug("Fallback search complete", hits=fallback_hits)
    if fallback_hits > 0:
        return fallback_result
    


def _extract_search_terms(query: Dict[str, Any]) -> List[str]:
    terms = []

    def extract_from_dict(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                if key in ["query", "match", "match_phrase", "term"]:
                    if isinstance(value, str):
                        terms.append(value)
                    elif isinstance(value, dict):
                        extract_from_dict(value, current_path)
                elif isinstance(value, (dict, list)):
                    extract_from_dict(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                item_path = f"{path}[{i}]"
                extract_from_dict(item, item_path)
        elif isinstance(obj, str) and len(obj.strip()) > 2:
            # Only add meaningful strings
            clean_term = obj.strip()
            if not clean_term.lower() in ["dan", "atau", "dengan", "yang", "di", "ke", "dari"]:
                terms.append(clean_term)

    extract_from_dict(query)
    unique_terms = list(set(terms))  # Remove duplicates

    return unique_terms
