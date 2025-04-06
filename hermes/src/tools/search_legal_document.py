from google import genai
from google.genai import types
from dotenv import load_dotenv
from sqlalchemy import text
from ..common.postgres import db
from ..common.ollama_client import infer
from ..common.gemini_client import client as gemini_client
import os, json
load_dotenv()

def legal_document_search(query: str) -> list[str]:
    """
    Get relevant legal documents from the database to help answer the user's question.
    Use this like you would use a search engine. If when answering the user's question, you need to get some information from the legal documents, 
    you can use this function to get the relevant legal documents.
    
    Args:
        query: question to be answered. doesn't have to be from user question. You can freely use this to get the answer that might help the user.
    Returns:
        list of relevant legal documents (pdf file name).
    """
    try:
        # Process the query for text search
        processed_query = ' & '.join(query.split())
        
        # Use tsquery directly instead of conversion from tsvector
        sparse_results = db.execute(
            text("""--sql
            SELECT DISTINCT chunk.document_id,
            ts_rank_cd(chunk.full_text_search, plainto_tsquery('indonesian', :query)) AS rank
            FROM legal_document_pages AS chunk
            WHERE chunk.full_text_search @@ plainto_tsquery('indonesian', :query)
            ORDER BY rank DESC
            LIMIT 5;
            """), parameters={"query": query}
        ).fetchall()
        document_names = [f"{result[0]}.pdf" for result in sparse_results]

        try:
            # Vector search using embeddings
            query_dense_vector = infer.embed(input=query, model="bge-m3").embeddings[0]
            dense_results = db.execute(
            text("""
            SELECT DISTINCT chunk.legal_document_id,
            (1 - (chunk.embedding <=> CAST(:query_embedding AS vector))) AS similarity
            FROM legal_document_chunks AS chunk
            JOIN legal_documents AS doc ON chunk.legal_document_id = doc.id
            WHERE chunk.embedding IS NOT NULL 
            AND (1 - (chunk.embedding <=> CAST(:query_embedding AS vector))) > 0.6
            ORDER BY similarity DESC
            LIMIT 5;
            """), parameters={"query_embedding": query_dense_vector}
            ).fetchall()

            for result in dense_results:
                if f"{result[0]}.pdf" not in document_names:
                    document_names.append(f"{result[0]}.pdf")
        except Exception as e:
            print(f"Error in dense search: {str(e)}")
            # Continue with sparse results only

        # Get related documents through metadata
        try:
            for document_name in document_names.copy():  # Use a copy to avoid modification during iteration
                doc_id = document_name.replace(".pdf", "")
                metadata = db.execute(
                    text("""--sql
                    SELECT dasar_hukum, mengubah, diubah_oleh,
                        mencabut, dicabut_oleh, melaksanakan_amanat_peraturan, dilaksanakan_oleh_peraturan_pelaksana
                    FROM legal_documents WHERE id = :id;
                    """), parameters={"id": doc_id}
                ).fetchone()

                if metadata:
                    for payload in metadata:
                        if payload is None:
                            continue
                        try:
                            print(f"Processing JSON payload: {type(payload)}")
                            
                            # Check if payload is a list
                            if isinstance(payload, list):
                                for item in payload:
                                    if isinstance(item, dict) and 'ref' in item and f"{item['ref']}.pdf" not in document_names:
                                        print(f"Adding {item['ref']}.pdf from metadata list")
                                        document_names.append(f"{item['ref']}.pdf")
                            # Check if payload is a dictionary
                            elif isinstance(payload, dict):
                                if 'ref' in payload and f"{payload['ref']}.pdf" not in document_names:
                                    print(f"Adding {payload['ref']}.pdf from metadata dict")
                                    document_names.append(f"{payload['ref']}.pdf")
                            else:
                                print(f"Unexpected payload type: {type(payload)}")
                                
                        except (json.JSONDecodeError, TypeError) as json_error:
                            print(f"Invalid JSON in column: {payload[:50]}... - Error: {str(json_error)}")
                            # Skip if the column is not valid JSON
                            continue
        except Exception as metadata_error:
            print(f"Error processing document metadata: {str(metadata_error)}")
            # Continue with existing document names

        return document_names
        
    except Exception as e:
        print(f"Error in legal document search: {str(e)}")
        return []  # Return empty list on any error