from .search_legal_document import search_legal_documents

def get_document_metadata(id: str):
    normalized_id = id.replace("Nomor_", "").replace("Tahun_", "").replace(".pdf", "")
    normalized_id = id.split("___")[0]
    docs = search_legal_documents({
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "_id": normalized_id
                        }
                    }
                ]
    }}})
    if docs is None or docs.get("hits") is None or len(docs.get("hits")) == 0:
        return None

    hit = docs.get("hits")[0]

    # Note: search_legal_documents() already returns normalized structure
    # with "id" and "source" fields (not "_id" and "_source")
    return {
        "_id": hit.get("id"),  # Use "id" from normalized hit
        "id": hit.get("id"),
        "source": hit.get("source"),
        "pasal": None  # Ensure it's document metadata, not pasal-specific
    }

def get_documents_metadata_batch(ids: list[str]):
    if not ids:
        return []
    
    # Normalize IDs
    normalized_ids = []
    for id in ids:
        nid = id.replace("Nomor_", "").replace("Tahun_", "").replace(".pdf", "")
        nid = nid.split("___")[0]
        normalized_ids.append(nid)
    
    # Remove duplicates
    normalized_ids = list(set(normalized_ids))

    docs = search_legal_documents({
        "query": {
            "terms": {
                "_id": normalized_ids
            }
        },
        "size": len(normalized_ids)
    })

    if docs is None or docs.get("hits") is None:
        return []

    results = []
    for hit in docs.get("hits"):
        results.append({
            "_id": hit.get("id"),
            "id": hit.get("id"),
            "source": hit.get("source"),
            "pasal": None
        })
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python retrieve_document_metadata.py <document_id>")
        sys.exit(1)
    
    document_id = sys.argv[1]
    metadata = get_document_metadata(document_id)
    if metadata:
        print(metadata)
    else:
        print("Document not found.")
        sys.exit(1)
    print(metadata)
    sys.exit(0)