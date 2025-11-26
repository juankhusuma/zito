
import time
from src.common.gemini_client import client as gemini_client
from src.utils.logger import HermesLogger
from google.genai import types
from ..config.llm import EVALUATOR_AGENT_PROMPT_INIT
from ..model.search import Questions, History

logger = HermesLogger("evaluator")

def evaluate_question(history: History):
    start_time = time.time()

    try:
        check_res = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=EVALUATOR_AGENT_PROMPT_INIT,
                response_mime_type="application/json",
                response_schema=Questions,
                temperature=0.2,
            ),
        )

        duration_ms = int((time.time() - start_time) * 1000)
        logger.debug("Question evaluated", duration_ms=duration_ms)
        return Questions.model_validate(check_res.parsed)

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("Question evaluation failed", duration_ms=duration_ms, error=str(e))
        return Questions(
            questions=["Apa yang ingin Anda ketahui?"],
            is_sufficient=True,
            classification="general"
        )