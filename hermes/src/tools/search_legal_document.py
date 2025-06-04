from dotenv import load_dotenv
from typing import Any, Dict, List
import os
import json
import requests
import time

load_dotenv()

# Define ES mapping schema for documentation purposes
ES_MAPPING_SCHEMA = {
    "metadata": {
        "Tipe Dokumen": "keyword",  # UU, PP, Perpres, etc.
        "Judul": "text (indonesian_analyzer)",
        "T.E.U.": "text",
        "Nomor": "keyword",
        "Bentuk": "keyword",
        "Bentuk Singkat": "keyword",
        "Tahun": "keyword",
        "Tempat Penetapan": "keyword",
        "Tanggal Penetapan": "date",  # Format: yyyy-MM-dd
        "Tanggal Pengundangan": "date",
        "Tanggal Berlaku": "date",
        "Sumber": "text",
        "Subjek": "keyword",
        "Status": "keyword",  # Berlaku, Dicabut, etc.
        "Bahasa": "keyword",
        "Lokasi": "keyword",
        "Bidang": "keyword"
    },
    "relations": {
        "Mengubah": "nested object array",
        "Diubah dengan": "nested object array",
        "Diubah sebagian dengan": "nested object array",
        "Mencabut": "nested object array",
        "Mengubah sebagian": "nested object array", 
        "Dicabut dengan": "nested object array",
        "Dicabut sebagian dengan": "nested object array",
        "Mencabut sebagian": "nested object array",
        "Menetapkan": "nested object array",
        "Ditetapkan dengan": "nested object array"
    },
    "files": {
        "file_id": "keyword",
        "filename": "text",
        "download_url": "text",
        "content": "text (indonesian_analyzer)"
    },
    "abstrak": "text (indonesian_analyzer)",
    "catatan": "text (indonesian_analyzer)"
}

def get_elasticsearch_auth() -> tuple:
    """
    Get the Elasticsearch authentication credentials from environment variables.
    
    Returns:
        Tuple containing username and password
    """
    print("🔐 Getting Elasticsearch authentication credentials...")
    es_user = os.getenv("ELASTICSEARCH_USER")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if es_user and es_password:
        print(f"✅ Found Elasticsearch credentials for user: {es_user}")
        return (es_user, es_password)
    else:
        print("❌ Elasticsearch credentials not found in environment variables")
        return None

def legal_document_search(query: dict) -> List[Dict[str, Any]]:
    """
    Basic search function for legal documents that returns results from Elasticsearch.
    Now includes fallback strategies.
    
    Args:
        query: Elasticsearch query in dict format
    
    Returns:
        List of search results
    """
    print("🔍 Starting legal_document_search...")
    print(f"📝 Input query: {json.dumps(query, default=str, indent=2)}")
    
    start_time = time.time()
    result = search_legal_documents_with_fallback(query)
    elapsed = time.time() - start_time
    
    print(f"⏱️ legal_document_search completed in {elapsed:.2f} seconds")
    
    if "error" in result:
        print(f"❌ Search error: {result['error']}")
        return []
    
    hits = result.get("hits", [])
    print(f"✅ Returning {len(hits)} search results")
    return hits

def search_legal_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced search tool for Gemini LLM to search legal documents with complete flexibility.
    The LLM can construct any valid Elasticsearch query and aggregations.
    
    Args:
        search_query: A dictionary containing:
            - query: Required. Elasticsearch query object
            - aggs: Optional. Elasticsearch aggregations
            - size: Optional. Number of results to return (default: 10)
            - from: Optional. Starting offset for pagination (default: 0)
            - sort: Optional. Sorting criteria
            - _source: Optional. Fields to include in the results
    
    Returns:
        Complete Elasticsearch response with hits and aggregations
    """
    print("🚀 Starting search_legal_documents...")
    print(f"📋 Raw search query: {json.dumps(search_query, default=str, indent=2)}")
    
    url = os.getenv("ELASTICSEARCH_URL", "https://chat.lexin.cs.ui.ac.id/elasticsearch/peraturan_indonesia/_search")
    print(f"🌐 Using Elasticsearch URL: {url}")
    
    print("🔐 Getting authentication...")
    auth = get_elasticsearch_auth()
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
            auth=auth,
            headers=headers,
            json=request_body,
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

def search_legal_documents_with_fallback(search_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced search with fallback strategies when initial search yields no results.
    
    Args:
        search_query: A dictionary containing Elasticsearch query and options
    
    Returns:
        Complete Elasticsearch response with hits and aggregations
    """
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
    if "bool" in original_query:
        print("✅ Found boolean query, attempting fallback 1...")
        fallback_query = search_query.copy()
        bool_query = original_query["bool"].copy()
        
        # Remove filters and must clauses, keep only should
        if "should" in bool_query:
            print(f"📝 Original boolean query has {len(bool_query['should'])} should clauses")
            fallback_query["query"] = {
                "bool": {
                    "should": bool_query["should"],
                    "minimum_should_match": 1
                }
            }
            print(f"🔄 Fallback 1 query: {json.dumps(fallback_query, default=str, indent=2)}")
            result = search_legal_documents(fallback_query)
            
            if result.get("total_hits", 0) > 0:
                elapsed = time.time() - start_time
                print(f"✅ Fallback 1 successful: {result.get('total_hits')} results in {elapsed:.2f} seconds")
                result["fallback_used"] = "relaxed_boolean"
                return result
            else:
                print("❌ Fallback 1 yielded no results")
        else:
            print("⚠️ Boolean query has no 'should' clauses, skipping fallback 1")
    else:
        print("⚠️ Not a boolean query, skipping fallback 1")
    
    # Fallback 2: Try a broader multi-field search if we can extract search terms
    print("3️⃣ Attempting fallback 2: Multi-field search...")
    search_terms = _extract_search_terms(original_query)
    print(f"🔍 Extracted search terms: {search_terms}")
    
    if search_terms:
        terms_str = " ".join(search_terms)
        print(f"📝 Combined search terms: '{terms_str}'")
        
        fallback_query = {
            "query": {
                "multi_match": {
                    "query": terms_str,
                    "fields": [
                        "metadata.Judul^2",
                        "abstrak^1.5", 
                        "files.content",
                        "metadata.Subjek",
                        "catatan"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": search_query.get("size", 10)
        }
        print(f"🔄 Fallback 2 query: {json.dumps(fallback_query, default=str, indent=2)}")
        result = search_legal_documents(fallback_query)
        
        if result.get("total_hits", 0) > 0:
            elapsed = time.time() - start_time
            print(f"✅ Fallback 2 successful: {result.get('total_hits')} results in {elapsed:.2f} seconds")
            result["fallback_used"] = "multi_field_fuzzy"
            return result
        else:
            print("❌ Fallback 2 yielded no results")
    else:
        print("⚠️ No search terms extracted, skipping fallback 2")
    
    # Fallback 3: Very broad search across all text fields
    print("4️⃣ Attempting fallback 3: Query string search...")
    if search_terms:
        query_str = " OR ".join(search_terms)
        print(f"📝 Query string: '{query_str}'")
        
        fallback_query = {
            "query": {
                "query_string": {
                    "query": query_str,
                    "fields": ["*"],
                    "default_operator": "OR",
                    "fuzziness": "AUTO"
                }
            },
            "size": search_query.get("size", 10)
        }
        print(f"🔄 Fallback 3 query: {json.dumps(fallback_query, default=str, indent=2)}")
        result = search_legal_documents(fallback_query)
        
        if result.get("total_hits", 0) > 0:
            elapsed = time.time() - start_time
            print(f"✅ Fallback 3 successful: {result.get('total_hits')} results in {elapsed:.2f} seconds")
            result["fallback_used"] = "query_string_broad"
            return result
        else:
            print("❌ Fallback 3 yielded no results")
    else:
        print("⚠️ No search terms available, skipping fallback 3")
    
    # Fallback 4: Get recent documents if all else fails
    print("5️⃣ Attempting fallback 4: Recent documents...")
    size_limit = min(search_query.get("size", 10), 5)
    print(f"📏 Limiting recent documents to {size_limit} results")
    
    fallback_query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {"metadata.Tanggal Penetapan": {"order": "desc", "missing": "_last"}},
            {"metadata.Tahun": {"order": "desc"}}
        ],
        "size": size_limit
    }
    print(f"🔄 Fallback 4 query: {json.dumps(fallback_query, default=str, indent=2)}")
    result = search_legal_documents(fallback_query)
    
    if result.get("total_hits", 0) > 0:
        elapsed = time.time() - start_time
        print(f"✅ Fallback 4 successful: {result.get('total_hits')} recent documents in {elapsed:.2f} seconds")
        result["fallback_used"] = "recent_documents"
        return result
    
    elapsed = time.time() - start_time
    print(f"💔 All fallback strategies failed after {elapsed:.2f} seconds")
    
    return {
        "total_hits": 0,
        "max_score": None,
        "hits": [],
        "message": "No documents found even with fallback strategies",
        "fallback_used": "none"
    }

def _extract_search_terms(query: Dict[str, Any]) -> List[str]:
    """
    Extract search terms from various query types for fallback searches.
    
    Args:
        query: Elasticsearch query object
        
    Returns:
        List of extracted search terms
    """
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

def get_schema_information() -> str:
    """
    Returns information about the Elasticsearch schema for the LLM.
    
    Returns:
        String containing schema documentation
    """
    schema_info = """
    SKEMA DATA DOKUMEN HUKUM:
    
    metadata:
      - Tipe Dokumen (keyword): Type of legal document (UU, PP, Perpres, etc.)
      - Judul (text): Title of the document, searchable using Indonesian analyzer
      - Nomor (keyword): Document number
      - Bentuk (keyword): Document form (e.g., "Undang-Undang")
      - Bentuk Singkat (keyword): Short form of document type (e.g., "UU")
      - Tahun (keyword): Year of document
      - Tempat Penetapan (keyword): Place of enactment
      - Tanggal Penetapan (date): Date of enactment (format: yyyy-MM-dd)
      - Tanggal Pengundangan (date): Date of promulgation (format: yyyy-MM-dd)
      - Tanggal Berlaku (date): Effective date (format: yyyy-MM-dd)
      - Status (keyword): Document status (e.g., "Berlaku", "Dicabut")
      - Other metadata fields: T.E.U., Sumber, Subjek, Bahasa, Lokasi, Bidang
    
    relations (nested objects):
      Common relation types:
      - Mengubah: Documents that this document changes
      - Diubah dengan: Documents that change this document
      - Mencabut: Documents this document revokes
      - Dicabut dengan: Documents that revoke this document
      - Menetapkan: Documents this document establishes
      - Ditetapkan dengan: Documents that establish this document
      - Each relation contains: id, title, description, url
    
    files (nested):
      - file_id (keyword): File identifier
      - filename (text): Name of the file
      - download_url (text): URL to download the file
      - content (text): Content of the file, searchable using Indonesian analyzer
    
    abstrak (text): Abstract of the document, searchable using Indonesian analyzer
    catatan (text): Notes about the document, searchable using Indonesian analyzer
    
    PANDUAN PENCARIAN:
    1. Gunakan match untuk pencarian dasar teks
    2. Gunakan match_phrase untuk pencarian frasa tepat
    3. Gunakan nested untuk mencari dalam files.content atau relations
    4. Gunakan bool dengan kombinasi must, should, filter untuk pencarian kompleks
    5. Gunakan range untuk pencarian rentang tanggal
    6. Gunakan aggs untuk mendapatkan statistik atau pengelompokan
    """
    return schema_info

def legal_search_rest_handler(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a legal search request from the REST API.
    
    Args:
        request_body: Dictionary containing the query parameters
        
    Returns:
        Search results
    """
    print("🌐 Starting legal_search_rest_handler...")
    print(f"📋 Request body: {json.dumps(request_body, default=str, indent=2)}")
    
    try:
        # Extract the query parameters
        print("🔍 Extracting query parameters...")
        query = request_body.get("query")
        
        if not query:
            print("❌ No query parameter found in request")
            return {"error": "Query parameter is required"}
        
        print(f"✅ Found query parameter: {json.dumps(query, default=str)}")
        
        # Build search parameters
        print("🔧 Building search parameters...")
        search_params = {
            "query": query,
            "size": request_body.get("size", 10),
        }
        print(f"📏 Size parameter: {search_params['size']}")
        
        # Add optional parameters if present
        optional_params = ["from", "sort", "aggs", "_source"]
        for param in optional_params:
            if param in request_body:
                search_params[param] = request_body[param]
                print(f"➕ Added optional parameter '{param}': {json.dumps(request_body[param], default=str)}")
            else:
                print(f"⚪ Optional parameter '{param}' not provided")
        
        print(f"🔧 Final search parameters: {json.dumps(search_params, default=str, indent=2)}")
        
        # Execute the search with fallback
        print("🚀 Executing search with fallback...")
        result = search_legal_documents_with_fallback(search_params)
        
        if "error" in result:
            print(f"❌ Search execution failed: {result['error']}")
        else:
            print(f"✅ Search execution successful: {result.get('total_hits', 0)} results")
        
        return result
    
    except Exception as e:
        error_msg = f"Exception in REST handler: {str(e)}"
        print(f"💥 Unexpected error in REST handler: {error_msg}")
        print(f"🔍 Exception type: {type(e).__name__}")
        return {
            "error": error_msg,
            "message": "Failed to execute search query. Please check your query syntax."
        }

def example_queries() -> Dict[str, Dict[str, Any]]:
    """
    Provides example Elasticsearch queries for the LLM to reference.
    These examples demonstrate common legal document search patterns.
    
    Returns:
        Dictionary of example queries
    """
    return {
        "basic_search": {
            "query": {
                "match": {
                    "metadata.Judul": "jabatan notaris"
                }
            },
            "size": 10
        },
        "boolean_search": {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"metadata.Judul": "notaris"}},
                        {"match": {"files.content": "kewenangan notaris"}}
                    ],
                    "filter": [
                        {"term": {"metadata.Status": "Berlaku"}}
                    ]
                }
            }
        },
        "nested_content_search": {
            "query": {
                "nested": {
                    "path": "files",
                    "query": {
                        "match": {
                            "files.content": "cyber notary"
                        }
                    }
                }
            }
        },
        "relation_search": {
            "query": {
                "nested": {
                    "path": "relations.Mengubah",
                    "query": {
                        "match": {
                            "relations.Mengubah.id": "uu-30-2004"
                        }
                    }
                }
            }
        },
        "aggregation_search": {
            "query": {
                "bool": {
                    "must": [
                        {"match_phrase": {"files.content": "kewenangan notaris"}}
                    ],
                    "filter": [
                        {"range": {"metadata.Tanggal Penetapan": {"gte": "2010-01-01"}}},
                        {"term": {"metadata.Bentuk Singkat": "UU"}}
                    ]
                }
            },
            "aggs": {
                "by_year": {
                    "terms": {
                        "field": "metadata.Tahun"
                    }
                }
            }
        },
        "specific_law_search": {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"metadata.Nomor": "2"}},
                        {"term": {"metadata.Tahun": "2014"}},
                        {"term": {"metadata.Bentuk Singkat": "UU"}}
                    ]
                }
            },
            "size": 1
        },
        "phrase_search": {
            "query": {
                "nested": {
                    "path": "files",
                    "query": {
                        "match_phrase": {
                            "files.content": "hak dan kewajiban notaris"
                        }
                    }
                }
            },
            "_source": ["metadata", "abstrak", "relations"]
        },
        "multi_field_search": {
            "query": {
                "multi_match": {
                    "query": "notaris elektronik",
                    "fields": ["metadata.Judul", "abstrak", "files.content"]
                }
            },
            "size": 10
        }
    }

def __main__():
    print("🚀 Initializing REST API Elasticsearch client...")
    print("📋 Running sample query for testing...")
    
    # Example usage
    sample_query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"abstrak": "notaris"}},
                    {"match": {"files.content": "notaris"}}
                ]
            }
        },
        "size": 5
    }
    
    print(f"🔍 Sample query: {json.dumps(sample_query, indent=2)}")
    
    start_time = time.time()
    results = search_legal_documents(sample_query)
    elapsed = time.time() - start_time
    
    print(f"⏱️ Sample query completed in {elapsed:.2f} seconds")
    print(f"📊 Found {results.get('total_hits', 0)} results")
    
    if results.get('hits'):
        first_hit = results.get('hits')[0]
        print(f"📝 First hit ID: {first_hit.get('id')}")
        print(f"🎯 First hit score: {first_hit.get('score')}")
        print(f"📄 First hit metadata: {json.dumps(first_hit.get('source', {}).get('metadata', {}), indent=2, default=str)}")
    else:
        print("❌ No hits found in sample query")

if __name__ == "__main__":
    __main__()