from typing import List
from src.common.gemini_client import client as gemini_client


def batch_embed_queries(queries: List[str], model: str = "text-embedding-004") -> List[List[float]]:
    """
    Generate embeddings for multiple queries in a single batch request.

    This reduces API latency by combining multiple embedding requests into one.
    Significantly faster than calling embed_content() individually for each query.

    Args:
        queries: List of text strings to embed
        model: Embedding model name (default: text-embedding-004)

    Returns:
        List of embedding vectors, one per input query

    Raises:
        Exception: If Gemini API call fails
    """
    if not queries:
        return []

    if len(queries) == 1:
        embed_res = gemini_client.models.embed_content(
            model=model,
            contents=[queries[0]]
        )
        return [[float(x) for x in embed_res.embeddings[0].values]]

    embed_res = gemini_client.models.batch_embed_contents(
        model=model,
        requests=[{"content": query} for query in queries]
    )

    return [
        [float(x) for x in embedding.values]
        for embedding in embed_res.embeddings
    ]
