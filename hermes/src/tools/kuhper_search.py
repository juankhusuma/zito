import os
import json
import time
import requests
from typing import Dict, Any, List
from src.common.gemini_client import client as gemini_client
from src.common.pinecone_client import kuhper_index

def kuhper_document_search(query: dict) -> List[Dict[str, Any]]:
    print("🔍 Starting legal_document_search...")
    print(f"📝 Input query: {json.dumps(query, default=str, indent=2)}")
    
    start_time = time.time()
    result = search_kuhper_documents_with_fallback(query)
    elapsed = time.time() - start_time
    
    print(f"⏱️ legal_document_search completed in {elapsed:.2f} seconds")
    
    if "error" in result:
        print(f"❌ Search error: {result['error']}")
        return []
    
    hits = result.get("hits", [])
    print(f"✅ Returning {len(hits)} search results")
    return hits

def search_legal_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    print("🚀 Starting search_legal_documents...")
    print(f"📋 Raw search query: {json.dumps(search_query, default=str, indent=2)}")
    
    url = "https://chat.lexin.cs.ui.ac.id/elasticsearch/kuhper/_search"
    print(f"🌐 Using Elasticsearch URL: {url}")
    
    print("🔐 Getting authentication...")
    headers = {"Content-Type": "application/json"}
    
    # Set defaults
    original_size = search_query.get("size")
    search_query["size"] = search_query.get("size", 10)
    print(f"📏 Size parameter - original: {original_size}, final: {search_query['size']}")
    
    try:
        # Execute the search using requests directly - don't wrap in another "query" object
        request_body = search_query
        print(f"📤 Sending request to Elasticsearch...")
        print(f"📄 Request body: {json.dumps(request_body, indent=2)}")
        
        request_start = time.time()
        print("⏳ Making HTTP request to Elasticsearch...")
        
        response = requests.post(
            url=url,
            headers=headers,
            json=request_body,
            auth=("elastic", "password"),
            timeout=30
        )
        
        request_time = time.time() - request_start
        print(f"📡 HTTP request completed in {request_time:.2f} seconds")
        print(f"📊 Response status code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"Elasticsearch returned status code {response.status_code}: {response.text}"
            print(f"❌ HTTP Error: {error_msg}")
            return {
                "error": error_msg,
                "message": "Failed to execute search query. Please check your query syntax."
            }
        
        print("✅ Received successful response from Elasticsearch")
        print("🔄 Parsing JSON response...")
        
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
        print(f"🔄 Processing {len(hits_data)} hits...")
        
        for i, hit in enumerate(hits_data):
            print(f"  📝 Processing hit {i+1}: ID={hit.get('_id')}, Score={hit.get('_score')}")
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
            
        print(f"✅ Successfully formatted response with {len(formatted_response['hits'])} hits")
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
        print(f"🔍 Exception type: {type(e).__name__}")
        return {
            "error": error_msg,
            "message": "Failed to execute search query. Please check your query syntax."
        }
    
def search_dense_kuhper_documents(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    embed_res = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=[query]
    )
    embeddings = [float(x) for x in embed_res.embeddings[0].values]
    print(f"🔍 Embedding generated for query: {embeddings[:5]}... (total {len(embeddings)} dimensions)")

    print(f"📦 Searching Pinecone index for top {top_k} documents...")
    response = kuhper_index.query(
        vector=embeddings,
        top_k=top_k,
        include_values=True,
        include_metadata=True
    )
    print(f"📊 Pinecone search returned {len(response.matches)} matches")

    return response.to_dict()

def search_kuhper_documents_with_fallback(search_query: Dict[str, Any]) -> Dict[str, Any]:
    print("🔄 Starting search_legal_documents_with_fallback...")
    print(f"📋 Initial search query: {json.dumps(search_query, default=str, indent=2)}")
    
    start_time = time.time()
    
    # Try the original query first
    print("1️⃣ Attempting primary search...")
    result = search_legal_documents(search_query)
    
    # If we got results or there was an error, return as is
    if "error" in result:
        print(f"❌ Primary search failed with error: {result['error']}")
        return result
    
    total_hits = result.get("total_hits", 0)
    print(f"📊 Primary search results: {total_hits} hits")
    
    if total_hits > 0:
        elapsed = time.time() - start_time
        print(f"✅ Primary search successful in {elapsed:.2f} seconds")
        return result
    
    print("⚠️ No results found in primary search, starting fallback strategies...")
    
    # Extract the original query for fallback modifications
    original_query = search_query.get("query", {})
    print(f"🔍 Extracted original query for fallback: {json.dumps(original_query, default=str)}")
    
    # Fallback 1: If it's a bool query, try with just the "should" clauses and lower minimum_should_match
    print("2️⃣ Checking for boolean query fallback...")
    fallback_query = {
        "query": {
            "match": {
                "content": " ".join(_extract_search_terms(original_query))
            },
            "size": search_query.get("size", 10),
        }
    }
    print(f"🔄 Fallback query: {json.dumps(fallback_query, default=str, indent=2)}")

    # Execute the fallback search
    fallback_result = search_legal_documents(fallback_query)
    if "error" in fallback_result:
        print(f"❌ Fallback search failed with error: {fallback_result['error']}")
        return fallback_result
    fallback_hits = fallback_result.get("total_hits", 0)
    print(f"📊 Fallback search results: {fallback_hits} hits")
    if fallback_hits > 0:
        elapsed = time.time() - start_time
        print(f"✅ Fallback search successful in {elapsed:.2f} seconds")
        return fallback_result
    
    print("⚠️ No results found in fallback search, trying search term extraction...")


def _extract_search_terms(query: Dict[str, Any]) -> List[str]:
    print("🔍 Starting search term extraction...")
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
                        print(f"    ✅ Found string term: '{value}'")
                        terms.append(value)
                    elif isinstance(value, dict):
                        print(f"    🔄 Found dict, recursing...")
                        extract_from_dict(value, current_path)
                elif isinstance(value, (dict, list)):
                    print(f"    🔄 Found {type(value).__name__}, recursing...")
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
                print(f"  ✅ Found meaningful string term: '{clean_term}'")
                terms.append(clean_term)
            else:
                print(f"  ⚠️ Skipping common word: '{clean_term}'")
    
    extract_from_dict(query)
    unique_terms = list(set(terms))  # Remove duplicates
    
    print(f"📊 Extraction complete: {len(terms)} total terms, {len(unique_terms)} unique terms")
    print(f"📝 Final unique terms: {unique_terms}")
    
    return unique_terms
