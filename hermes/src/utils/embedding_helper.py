from typing import List
from src.common.gemini_client import client as gemini_client


def batch_embed_queries(queries: List[str], model: str = "text-embedding-004") -> List[List[float]]:
    """
    Generate embeddings for multiple queries in a single batch request.

    Falls back to sequential embedding if batch_embed_contents is unavailable.

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

    if hasattr(gemini_client.models, 'batch_embed_contents'):
        embed_res = gemini_client.models.batch_embed_contents(
            model=model,
            requests=[{"content": query} for query in queries]
        )
        return [
            [float(x) for x in embedding.values]
            for embedding in embed_res.embeddings
        ]
    else:
        results = []
        for query in queries:
            embed_res = gemini_client.models.embed_content(
                model=model,
                contents=[query]
            )
            results.append([float(x) for x in embed_res.embeddings[0].values])
        return results
