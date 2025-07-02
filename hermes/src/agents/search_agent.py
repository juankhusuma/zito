

import time
import json
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import MODEL_NAME, SEARCH_AGENT_PROMPT, REWRITE_PROMPT
from ..tools.search_legal_document import legal_document_search

def evaluate_es_query(query: dict):
    try:
        documents = legal_document_search(query=query)
        return (documents, None)
    except Exception as e:
        print(f"Error searching legal documents: {str(e)}")
        return (None, str(e))

def generate_and_execute_es_query(questions: list[str]):
    time.sleep(1)
    last_no_hit = False
    prev_query = None
    max_attempt = 3
    while True and max_attempt > 0:
        max_attempt -= 1
        es_query_res = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[{
                "role": "user",
                "parts": [
                    {
                        "text": "\n".join(["- " + question for question in questions])
                    }
                ],
            }],
            config=types.GenerateContentConfig(
                system_instruction=SEARCH_AGENT_PROMPT + \
                    "" if not last_no_hit else REWRITE_PROMPT(prev_query),
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        query_json = None
        try:
            query_json = json.loads(es_query_res.text)
        except json.JSONDecodeError:
            print("Error decoding JSON response from Gemini")
            continue
        documents, error = evaluate_es_query(query_json)
        if len(documents) == 0:
            last_no_hit = True
            continue
        if error is None:
            return documents[:5]
        time.sleep(1)

