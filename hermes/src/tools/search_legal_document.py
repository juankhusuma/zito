from dotenv import load_dotenv
from typing import Any, Dict, List
import os
import json
import requests

load_dotenv()

# Define ES mapping schema for documentation purposes
ES_MAPPING_SCHEMA = {
    "metadata": {
        "Tipe Dokumen": "keyword",
        "Judul": "text (indonesian_analyzer)",
        "T.E.U.": "text",
        "Nomor": "keyword",
        "Bentuk": "keyword",
        "Bentuk Singkat": "keyword",
        "Tahun": "keyword",
        "Tempat Penetapan": "keyword",
        "Tanggal Penetapan": "date",
        "Tanggal Pengundangan": "date",
        "Tanggal Berlaku": "date",
        "Sumber": "text",
        "Subjek": "keyword",
        "Status": "keyword",
        "Bahasa": "keyword",
        "Lokasi": "keyword",
        "Bidang": "keyword"
    },
    "relations": "object",
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
    Available fields for querying legal documents:
    
    metadata:
      - Tipe Dokumen (keyword): Type of legal document
      - Judul (text): Title of the document, searchable using Indonesian analyzer
      - T.E.U. (text): T.E.U. information
      - Nomor (keyword): Document number
      - Bentuk (keyword): Document form
      - Bentuk Singkat (keyword): Short form of document type
      - Tahun (keyword): Year
      - Tempat Penetapan (keyword): Place of enactment
      - Tanggal Penetapan (date): Date of enactment (format: yyyy-MM-dd)
      - Tanggal Pengundangan (date): Date of promulgation (format: yyyy-MM-dd)
      - Tanggal Berlaku (date): Effective date (format: yyyy-MM-dd)
      - Sumber (text): Source
      - Subjek (keyword): Subject
      - Status (keyword): Status
      - Bahasa (keyword): Language
      - Lokasi (keyword): Location
      - Bidang (keyword): Field/area
    
    files (nested):
      - file_id (keyword): File identifier
      - filename (text): Name of the file
      - download_url (text): URL to download the file
      - content (text): Content of the file, searchable using Indonesian analyzer
    
    abstrak (text): Abstract of the document, searchable using Indonesian analyzer
    catatan (text): Notes about the document, searchable using Indonesian analyzer
    """
    return schema_info

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
        "basic_keyword_search": {
            "query": {
                "match": {
                    "metadata.Judul": "pajak"
                }
            }
        },
        "law_by_number": {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"metadata.Nomor": "13"}},
                        {"term": {"metadata.Tahun": "2003"}}
                    ]
                }
            },
            "size": 1
        },
        "document_by_topic": {
            "query": {
                "multi_match": {
                    "query": "hukum acara pidana",
                    "fields": ["metadata.Judul^3", "abstrak^2", "files.content"],
                    "type": "cross_fields",
                    "operator": "and"
                }
            },
            "size": 5,
            "_source": ["metadata.Judul", "metadata.Nomor", "metadata.Tahun", "metadata.Bentuk", "abstrak"]
        },
        "nested_content_search": {
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
            "size": 5
        },
        "notaris_search": {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"metadata.Judul": "notaris"}},
                        {"match": {"abstrak": "hak dan wewenang notaris"}},
                        {"match": {"files.content": "hak dan wewenang notaris"}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 5,
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        },
        "multi_field_search": {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"metadata.Judul": "pidana"}},
                        {"term": {"metadata.Tahun": "2023"}}
                    ]
                }
            }
        },
        "full_text_search": {
            "query": {
                "multi_match": {
                    "query": "hak asasi manusia",
                    "fields": ["metadata.Judul", "abstrak", "files.content"]
                }
            }
        },
        "date_range_search": {
            "query": {
                "range": {
                    "metadata.Tanggal Penetapan": {
                        "gte": "2020-01-01",
                        "lte": "2023-12-31"
                    }
                }
            }
        },
        "aggregation_example": {
            "size": 0,
            "aggs": {
                "document_types": {
                    "terms": {
                        "field": "metadata.Tipe Dokumen",
                        "size": 10
                    }
                },
                "yearly_stats": {
                    "terms": {
                        "field": "metadata.Tahun",
                        "size": 10,
                        "order": {"_key": "desc"}
                    }
                }
            }
        },
        "complex_search": {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"metadata.Judul": "penyelenggaraan"}},
                        {"term": {"metadata.Bentuk": "PERATURAN"}}
                    ],
                    "filter": [
                        {"range": {"metadata.Tanggal Penetapan": {"gte": "2018-01-01"}}},
                        {"term": {"metadata.Status": "Berlaku"}}
                    ],
                    "should": [
                        {"match": {"abstrak": "pemerintahan daerah"}},
                        {"match": {"files.content": "otonomi daerah"}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 20,
            "sort": [
                {"metadata.Tanggal Penetapan": {"order": "desc"}}
            ],
            "aggs": {
                "by_year": {
                    "terms": {"field": "metadata.Tahun"}
                }
            }
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