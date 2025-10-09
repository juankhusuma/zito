
import time
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import EVALUATOR_AGENT_PROMPT_INIT
from ..model.search import Questions, History

def evaluate_question(history: History):
    start_time = time.time()
    print(f"DEBUG: evaluate_question started at {start_time}")
    
    try:
        check_res = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=EVALUATOR_AGENT_PROMPT_INIT,
                response_mime_type="application/json",
                response_schema=Questions,
                temperature=0.2,
                timeout=30  # Add 30 second timeout
            ),
        )
        
        end_time = time.time()
        print(f"DEBUG: evaluate_question done in {end_time - start_time:.2f} seconds")
        return Questions.model_validate(check_res.parsed)
        
    except Exception as e:
        end_time = time.time()
        print(f"DEBUG: evaluate_question error after {end_time - start_time:.2f} seconds: {e}")
        # Return default response instead of crashing
        return Questions(questions=["Apa yang ingin Anda ketahui?"])
