from src.common.gemini_client import client as gemini_client
from google.genai import types
from ..config.llm import GENERATE_TITLE_AGENT_PROMPT
from ..model.search import History

def generate_title(history: History):
    title_res = gemini_client.models.generate_content(
        model="gemini-1.5-flash-002",
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=GENERATE_TITLE_AGENT_PROMPT,
            max_output_tokens=500,
        ),
    )
    return title_res.text