
from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import EVALUATOR_AGENT_PROMPT_INIT
from ..model.search import Questions, History

def evaluate_question(history: History):
    check_res = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=EVALUATOR_AGENT_PROMPT_INIT,
            response_mime_type="application/json",
            response_schema=Questions,
            temperature=0.2,
        ),
    )
    return Questions.model_validate(check_res.parsed)
