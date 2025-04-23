from dotenv import load_dotenv
from typing import Any, Dict, List
import os
import json
import requests

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

def get_elasticsearch_url() -> str:
    """
    Get the Elasticsearch URL from environment variables.
    
    Returns:
        String containing the Elasticsearch URL
    """
    es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
    return f"http://{es_host}:{es_port}"

def get_elasticsearch_auth() -> tuple:
    """
    Get the Elasticsearch authentication credentials from environment variables.
    
    Returns:
        Tuple containing username and password
    """
    es_user = os.getenv("ELASTICSEARCH_USER")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD")
    return (es_user, es_password) if es_user and es_password else None

def legal_document_search(query: dict) -> List[Dict[str, Any]]:
    """
    Basic search function for legal documents that returns results from Elasticsearch.
    
    Args:
        query: Elasticsearch query in dict format
    
    Returns:
        List of search results
    """
    url = f"{get_elasticsearch_url()}/peraturan_indonesia/_search"
    auth = get_elasticsearch_auth()
    headers = {"Content-Type": "application/json"}
    
    # The query should be directly included in the request body, not nested under a "query" key again
    request_body = query
    try:
        print(f"Sending request to Elasticsearch: {json.dumps(request_body, indent=2)}")
        response = requests.post(
            url=url,
            auth=auth,
            headers=headers,
            json=request_body
        )
        
        if response.status_code != 200:
            print(f"Elasticsearch error ({response.status_code}): {response.text}")
            return []
            
        data = response.json()
        print("Received response from Elasticsearch: ", len(data.get("hits", {}).get("hits", [])), " hits found.")
        return data.get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"Error searching Elasticsearch: {str(e)}")
        return []

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

def search_legal_documents(search_query: Dict[str, Any]) -> Dict[str, Any]:
    print(search_query)
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
    url = f"{get_elasticsearch_url()}/peraturan_indonesia/_search"
    auth = get_elasticsearch_auth()
    headers = {"Content-Type": "application/json"}
    
    # Set defaults
    if "size" not in search_query:
        search_query["size"] = 10
    
    try:
        # Execute the search using requests directly - don't wrap in another "query" object
        request_body = search_query
        print(f"Sending request to Elasticsearch: {json.dumps(request_body, indent=2)}")
        
        response = requests.post(
            url=url,
            auth=auth,
            headers=headers,
            json=request_body
        )
        
        if response.status_code != 200:
            error_msg = f"Elasticsearch returned status code {response.status_code}: {response.text}"
            print(error_msg)
            return {
                "error": error_msg,
                "message": "Failed to execute search query. Please check your query syntax."
            }
        
        data = response.json()
        
        # Format the response to be more user-friendly
        formatted_response = {
            "total_hits": data.get("hits", {}).get("total", {}).get("value", 0),
            "max_score": data.get("hits", {}).get("max_score"),
            "hits": []
        }
        
        # Process hits
        for hit in data.get("hits", {}).get("hits", []):
            formatted_hit = {
                "score": hit.get("_score"),
                "id": hit.get("_id"),
                "source": hit.get("_source", {})
            }
            formatted_response["hits"].append(formatted_hit)
        
        # Include aggregations if present
        if "aggregations" in data:
            formatted_response["aggregations"] = data["aggregations"]
            
        print(formatted_response)
        return formatted_response
        
    except Exception as e:
        error_msg = f"Failed to execute search query: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "message": "Failed to execute search query. Please check your query syntax."
        }

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
        if "from" in request_body:
            search_params["from"] = request_body["from"]
        
        if "sort" in request_body:
            search_params["sort"] = request_body["sort"]
            
        if "aggs" in request_body:
            search_params["aggs"] = request_body["aggs"]
            
        if "_source" in request_body:
            search_params["_source"] = request_body["_source"]
        
        # Execute the search
        return search_legal_documents(search_params)
    
    except Exception as e:
        return {
            "error": str(e),
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
    print("REST API Elasticsearch client initialized.")
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
    
    results = search_legal_documents(sample_query)
    print(f"Found {results.get('total_hits', 0)} results")
    if results.get('hits'):
        print(f"First hit: {json.dumps(results.get('hits')[0], indent=2)}")
    else:
        print("No hits found.")

if __name__ == "__main__":
    __main__()