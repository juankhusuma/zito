from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()

def get_elasticsearch_client() -> Elasticsearch:
    """
    Create an Elasticsearch client using environment variables for configuration.
    
    Returns:
        Elasticsearch: An instance of the Elasticsearch client.
    """
    es_host = os.getenv("ELASTICSEARCH_HOST", "chat.lexin.cs.ui.ac.id/elasticsearch")
    es_port = os.getenv("ELASTICSEARCH_PORT", 9200)
    es_user = os.getenv("ELASTICSEARCH_USER", "elastic")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD", "password")

    es = Elasticsearch(
        [f"http://{es_host}:{es_port}"],
        http_auth=(es_user, es_password),
        scheme="http",
        port=es_port,
    )

    return es