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
    return docs.get("hits")[0]

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