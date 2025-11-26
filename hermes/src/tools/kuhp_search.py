import os
import json
import time
import requests
from typing import Dict, Any, List
from src.common.gemini_client import client as gemini_client
from src.common.pinecone_client import kuhp_index
from src.utils.logger import HermesLogger

logger = HermesLogger("kuhp_search")

def kuhp_document_search(query: dict) -> List[Dict[str, Any]]:
    start_time = time.time()
    result = search_kuhp_documents_with_fallback(query)
    elapsed = time.time() - start_time

    if "error" in result:
        logger.error("KUHP search failed", error=result['error'])
        return []

    hits = result.get("hits", [])
    logger.info("KUHP search complete", hits=len(hits), duration_ms=int(elapsed * 1000))
    return hits

def search_legal_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    
    url = f"{os.environ.get("ES_BASE_URL", "https://chat.lexin.cs.ui.ac.id/elasticsearch")}/kuhp/_search"

    es_user = os.environ.get("ELASTICSEARCH_USER")
    es_password = os.environ.get("ELASTICSEARCH_PASSWORD")

    if es_user and es_password:
        auth = (es_user, es_password)
    else:
        auth = None

    headers = {"Content-Type": "application/json"}
    
    # Set defaults
    original_size = search_query.get("size")
    search_query["size"] = search_query.get("size", 10)
    print(f"📏 Size parameter - original: {original_size}, final: {search_query['size']}")
    
    try:
        # Execute the search using requests directly - don't wrap in another "query" object
        request_body = search_query
        print(f"📤 Sending request to Elasticsearch...")
        
        request_start = time.time()
        print("⏳ Making HTTP request to Elasticsearch...")
        
        response = requests.post(
            url=url,
            headers=headers,
            json=request_body,
            auth=auth,
            timeout=30
        )
        
        request_time = time.time() - request_start
        print(f"📊 Response status code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"Elasticsearch returned status code {response.status_code}: {response.text}"
            return {
                "error": error_msg,
                "message": "Failed to execute search query. Please check your query syntax."
            }
        
        
        data = response.json()
        print(f"📈 Raw response total hits: {data.get('hits', {}).get('total', {}).get('value', 0)}")
        print(f"🎯 Raw response max score: {data.get('hits', {}).get('max_score')}")
        
        # Format the response to be more user-friendly
        total_hits = data.get("hits", {}).get("total", {}).get("value", 0)
        max_score = data.get("hits", {}).get("max_score")
        
        print(f"📊 Formatting response - total_hits: {total_hits}, max_score: {max_score}")
        
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
            agg_keys = list(data["aggregations"].keys())
            print(f"📊 Found aggregations: {agg_keys}")
            formatted_response["aggregations"] = data["aggregations"]
        else:
            print("📊 No aggregations in response")
            
        return formatted_response
        
    except requests.exceptions.Timeout:
        error_msg = "Elasticsearch request timed out after 30 seconds"
        print(f"⏰ Timeout error: {error_msg}")
        return {
            "error": error_msg,
            "message": "Search request timed out. Please try again or refine your query."
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to Elasticsearch: {str(e)}"
        print(f"🔌 Connection error: {error_msg}")
        return {
            "error": error_msg,
            "message": "Unable to connect to search service. Please try again later."
        }
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse Elasticsearch response: {str(e)}"
        print(f"🔧 JSON parsing error: {error_msg}")
        return {
            "error": error_msg,
            "message": "Invalid response from search service."
        }
    except Exception as e:
        error_msg = f"Failed to execute search query: {str(e)}"
        print(f"💥 Unexpected error: {error_msg}")
        return {
            "error": error_msg,
            "message": "Failed to execute search query. Please check your query syntax."
        }
    
def search_dense_kuhp_documents(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    embed_res = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=[query]
    )
    embeddings = [float(x) for x in embed_res.embeddings[0].values]

    print(f"📦 Searching Pinecone index for top {top_k} documents...")
    response = kuhp_index.query(
        vector=embeddings,
        top_k=top_k,
        include_values=True,
        include_metadata=True
    )
    print(f"📊 Pinecone search returned {len(response.matches)} matches")

    return response.to_dict()

def search_kuhp_documents_with_fallback(search_query: Dict[str, Any]) -> Dict[str, Any]:
    
    start_time = time.time()
    
    # Try the original query first
    result = search_legal_documents(search_query)
    
    # If we got results or there was an error, return as is
    if "error" in result:
        return result
    
    total_hits = result.get("total_hits", 0)
    print(f"📊 Primary search results: {total_hits} hits")
    
    if total_hits > 0:
        elapsed = time.time() - start_time
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
    print(f"📊 Fallback search results: {fallback_hits} hits")
    if fallback_hits > 0:
        elapsed = time.time() - start_time
        return fallback_result
    


def _extract_search_terms(query: Dict[str, Any]) -> List[str]:
    print(f"📋 Input query for extraction: {json.dumps(query, default=str)}")
    
    terms = []
    
    def extract_from_dict(obj, path=""):
        print(f"  🔎 Examining object at path '{path}': {type(obj).__name__}")
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                print(f"    🔑 Processing key '{key}' at path '{current_path}'")
                
                if key in ["query", "match", "match_phrase", "term"]:
                    if isinstance(value, str):
                        terms.append(value)
                    elif isinstance(value, dict):
                        extract_from_dict(value, current_path)
                elif isinstance(value, (dict, list)):
                    extract_from_dict(value, current_path)
        elif isinstance(obj, list):
            print(f"  📋 Processing list with {len(obj)} items")
            for i, item in enumerate(obj):
                item_path = f"{path}[{i}]"
                extract_from_dict(item, item_path)
        elif isinstance(obj, str) and len(obj.strip()) > 2:
            # Only add meaningful strings
            clean_term = obj.strip()
            if not clean_term.lower() in ["dan", "atau", "dengan", "yang", "di", "ke", "dari"]:
                terms.append(clean_term)
            else:
    
    extract_from_dict(query)
    unique_terms = list(set(terms))  # Remove duplicates
    
    print(f"📊 Extraction complete: {len(terms)} total terms, {len(unique_terms)} unique terms")
    
    return unique_terms