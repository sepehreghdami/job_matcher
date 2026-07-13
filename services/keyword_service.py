# services/keyword_service.py

import logging
from typing import List
from pydantic import BaseModel
from agents import Agent, Runner
from config import settings
from openai import AsyncOpenAI
from agents import set_default_openai_client
from services.scoring_constants import KEYWORD_EXTRACTION_INSTRUCTIONS
import agents

agents.set_tracing_disabled(True)

logger = logging.getLogger(__name__)

MIN_RESUME_LEN = 50


class KeywordExtractionResult(BaseModel):
    keywords: List[str]


_client = None
_agent = None


def _ensure_initialized():
    global _client, _agent
    if _client is None:
        logger.info("Initializing keyword extraction LLM client (model=%s)", settings.scoring_model)
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        set_default_openai_client(_client)
        _agent = Agent(
            name="resume_keyword_extractor",
            model=settings.scoring_model,
            instructions=KEYWORD_EXTRACTION_INSTRUCTIONS,
            output_type=KeywordExtractionResult,
        )


async def extract_keywords(resume_text: str) -> List[str]:
    """
    Extract a deduplicated, lowercase keyword list from a resume via the LLM.

    Returns an empty list (never raises) if the resume is too short or the
    LLM call fails — callers must not be blocked by extraction failures.
    """
    if not resume_text or len(resume_text.strip()) < MIN_RESUME_LEN:
        return []

    _ensure_initialized()

    try:
        prompt = f"RESUME:\n{resume_text.strip()}"
        result = await Runner.run(_agent, prompt)
        parsed: KeywordExtractionResult = result.final_output
    except Exception as e:
        logger.warning("[keywords] extraction failed: %s: %s", type(e).__name__, e)
        return []

    keywords = list(dict.fromkeys(k.strip().lower() for k in parsed.keywords if k.strip()))

    logger.info("[keywords] extracted %d keywords from resume (%d chars)", len(keywords), len(resume_text))
    return keywords
