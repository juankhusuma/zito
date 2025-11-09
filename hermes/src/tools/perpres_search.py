import os
import json
import time
import requests
from typing import Dict, Any, List
from src.common.gemini_client import client as gemini_client
from src.common.pinecone_client import perpres_index
from dotenv import load_dotenv
load_dotenv()

def perpres_document_search(query: dict) -> List[Dict[str, Any]]:
    print("🔍 Starting perpres_document_search...")
    print(f"📝 Input query: {json.dumps(query, default=str, indent=2)}")
    
    start_time = time.time()
    result = search_perpres_documents_with_fallback(query)
    elapsed = time.time() - start_time
    
    print(f"⏱️ perpres_document_search completed in {elapsed:.2f} seconds")
    
    if "error" in result:
        print(f"❌ Search error: {result['error']}")
        return []
    
    hits = result.get("hits", [])
    print(f"✅ Returning {len(hits)} search results")
    return hits

def search_perpres_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    print("🚀 Starting search_perpres_documents...")
    
    url = f"{os.environ.get('ES_BASE_URL', 'https://chat.lexin.cs.ui.ac.id/elasticsearch')}/perpres/_search"
    print(f"🌐 Using Elasticsearch URL: {url}")
    
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
            error_msg = f"Elasticsearch returned status code {response.status_code}: {response.text}"
            print(f"❌ HTTP Error: {error_msg}")
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
        
        print(f"✅ Successfully retrieved {formatted_response['total_hits']} perpres documents")
        return formatted_response
        
    except Exception as e:
        error_msg = f"Error executing perpres search: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

def search_perpres_documents_with_fallback(original_query: Dict[str, Any]) -> Dict[str, Any]:
    print("🔄 Starting search with fallback for perpres...")
    start_time = time.time()
    
    # Try original query first
    result = search_perpres_documents(original_query)
    if "error" not in result and result.get("total_hits", 0) > 0:
        print(f"✅ Original query successful")
        return result
    
    # Fallback: simple match query
    print("⚠️ Original query returned no results, trying fallback...")
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
    print(f"🔍 Pinecone dense search for perpres: '{query}' (k={k})")
    
    try:
        # Generate embedding using Gemini
        res = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=query
        )
        query_embedding = res.embeddings[0].values
        
        # Search Pinecone
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
        
        print(f"✅ Pinecone perpres search returned {len(documents)} documents")
        return documents
        
    except Exception as e:
        print(f"❌ Pinecone perpres search failed: {e}")
        return []
