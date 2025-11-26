from dotenv import load_dotenv
from typing import Any, Dict, List
import os
import json
import requests
import time
from src.utils.logger import HermesLogger

load_dotenv()

logger = HermesLogger("legal_doc_search")

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
    es_user = os.getenv("ELASTICSEARCH_USER")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD")
    
    if es_user and es_password:
        return (es_user, es_password)
    else:
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
    
    start_time = time.time()
    result = search_legal_documents_with_fallback(query)
    elapsed = time.time() - start_time
    
    
    if "error" in result:
        return []
    
    hits = result.get("hits", [])
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
    
    url = f"{os.environ.get('ES_BASE_URL', 'https://chat.lexin.cs.ui.ac.id/elasticsearch')}/peraturan_indonesia/_search"
    
    auth = get_elasticsearch_auth()
    headers = {"Content-Type": "application/json"}
    
    # Set defaults
    original_size = search_query.get("size")
    search_query["size"] = search_query.get("size", 10)

    
    try:
        # Execute the search using requests directly - don't wrap in another "query" object
        request_body = search_query

        request_start = time.time()

        response = requests.post(
            url=url,
            auth=auth,
            headers=headers,
            json=request_body,
            timeout=30,
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
            agg_keys = list(data["aggregations"].keys())

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

def search_legal_documents_with_fallback(search_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced search with fallback strategies when initial search yields no results.
    
    Args:
        search_query: A dictionary containing Elasticsearch query and options
    
    Returns:
        Complete Elasticsearch response with hits and aggregations
    """
    
    start_time = time.time()
    
    # Try the original query first
    result = search_legal_documents(search_query)
    
    # If we got results or there was an error, return as is
    if "error" in result:
        return result
    
    total_hits = result.get("total_hits", 0)

    
    if total_hits > 0:
        elapsed = time.time() - start_time
        return result
    
    
    # Extract the original query for fallback modifications
    original_query = search_query.get("query", {})
    
    # Fallback 1: If it's a bool query, try with just the "should" clauses and lower minimum_should_match
    if "bool" in original_query:
        fallback_query = search_query.copy()
        bool_query = original_query["bool"].copy()
        
        # Remove filters and must clauses, keep only should
        if "should" in bool_query:
            fallback_query["query"] = {
                "bool": {
                    "should": bool_query["should"],
                    "minimum_should_match": 1
                }
            }
            result = search_legal_documents(fallback_query)

            if result.get("total_hits", 0) > 0:
                elapsed = time.time() - start_time
                result["fallback_used"] = "relaxed_boolean"
                return result
    
    # Fallback 2: Try a broader multi-field search if we can extract search terms
    search_terms = _extract_search_terms(original_query)
    
    if search_terms:
        terms_str = " ".join(search_terms)
        
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
        result = search_legal_documents(fallback_query)
        
        if result.get("total_hits", 0) > 0:
            elapsed = time.time() - start_time
            result["fallback_used"] = "multi_field_fuzzy"
            return result
    
    # Fallback 3: Very broad search across all text fields
    if search_terms:
        query_str = " OR ".join(search_terms)
        
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
        result = search_legal_documents(fallback_query)
        
        if result.get("total_hits", 0) > 0:
            elapsed = time.time() - start_time
            result["fallback_used"] = "query_string_broad"
            return result
    
    # Fallback 4: Get recent documents if all else fails
    size_limit = min(search_query.get("size", 10), 5)

    
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
    result = search_legal_documents(fallback_query)
    
    if result.get("total_hits", 0) > 0:
        elapsed = time.time() - start_time
        result["fallback_used"] = "recent_documents"
        return result
    
    elapsed = time.time() - start_time
    
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
    
    try:
        # Extract the query parameters
        query = request_body.get("query")
        
        if not query:
            return {"error": "Query parameter is required"}
        
        # Build search parameters
        search_params = {
            "query": query,
            "size": request_body.get("size", 10),
        }

        # Add optional parameters if present
        optional_params = ["from", "sort", "aggs", "_source"]
        for param in optional_params:
            if param in request_body:
                search_params[param] = request_body[param]

        # Execute the search with fallback
        result = search_legal_documents_with_fallback(search_params)

        if "error" in result:
            return result

        return result

    except Exception as e:
        error_msg = f"Exception in REST handler: {str(e)}"
        logger.error("REST handler error", error=error_msg)
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
    logger.info("Running sample query for testing")

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

    start_time = time.time()
    results = search_legal_documents(sample_query)
    elapsed = time.time() - start_time

    if results.get('hits'):
        first_hit = results.get('hits')[0]
        logger.info("Test query complete", score=first_hit.get('score'), duration_ms=int(elapsed * 1000))

if __name__ == "__main__":
    __main__()