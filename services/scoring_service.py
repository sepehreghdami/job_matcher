# services/scoring.py

import asyncio
from typing import List
from pydantic import BaseModel
from agents import Agent, Runner
from schemas.telegram_message import TelegramMessage
from schemas.user import UserDto
from schemas.evaluation import EvaluationDto
from datetime import datetime, timezone
from config import settings  # BATCH_SIZE lives here


# ── Output schema ────────────────────────────────────────────────────────────
# The agent is forced to return this exact shape.
# message_pk echoes back what we sent — this solves your identity problem.

class MessageScore(BaseModel):
    message_pk: int
    score: float           # 1.0 – 10.0
    reason: str            # one-sentence justification — useful for debugging


class ScoringResult(BaseModel):
    scores: List[MessageScore]


# ── Prompts ───────────────────────────────────────────────────────────────────

INSTRUCTIONS = """
You are a senior technical recruiter with 15 years of experience matching 
candidates to roles across software engineering, data, and product.

Your task:
Given a candidate resume and a batch of job postings, score each posting 
on how well the candidate's background matches the role requirements.

Scoring rules:
- Score range: 1.0 to 10.0 (one decimal place)
- 1–3 : Poor match. Candidate lacks core required skills or the role is in 
        a completely different domain.
- 4–6 : Partial match. Candidate meets some requirements but has clear gaps 
        in either skills, seniority, or domain.
- 7–8 : Good match. Candidate meets most requirements. Minor gaps only.
- 9–10: Excellent match. Candidate exceeds or precisely fits the requirements.

Rules you must follow:
- Base your score ONLY on the resume and posting text provided.
- Do not infer or assume skills not mentioned in the resume.
- If a posting is not a job opportunity (spam, irrelevant), assign score 1.
- You MUST return a score for EVERY message_pk provided — no skipping.
- The `reason` field must be one sentence explaining the key factor behind the score.
"""

# Opinion: keep the user prompt as a pure data envelope — no instructions here.
# All behavioral instructions belong in the system prompt above.
# This separation makes prompt tuning easier and avoids confusion.

def _build_user_prompt(resume: str, messages: List[TelegramMessage]) -> str:
    postings = "\n\n".join(
        f"message_pk: {msg.pk}\n{(msg.text or '').strip()[:500]}"
        for msg in messages
    )
    return f"""
CANDIDATE RESUME:
{resume.strip()}

JOB POSTINGS:
{postings}
"""


# ── Agent ─────────────────────────────────────────────────────────────────────

# Opinion: create the agent once at module level — it's stateless config,
# no reason to rebuild it on every call.

_agent = Agent(
    name="job_opportunity_evaluator",
    instructions=INSTRUCTIONS,
    output_type=ScoringResult,   # forces structured output, no JSON parsing needed
)


# ── Core coroutine ────────────────────────────────────────────────────────────

async def _score_batch(
    user: UserDto,
    batch: List[TelegramMessage],
) -> List[EvaluationDto]:
    """Score one batch of messages against a user resume. Returns EvaluationDtos."""

    prompt = _build_user_prompt(resume=user.resume_text, messages=batch)
    result = await Runner.run(_agent, prompt)

    # result.final_output is already a ScoringResult — no JSON parsing
    scored: ScoringResult = result.final_output

    now = datetime.now(timezone.utc)

    # build a quick lookup so we can validate the LLM echoed all pks back
    sent_pks = {msg.pk for msg in batch}
    returned_pks = {s.message_pk for s in scored.scores}
    missing = sent_pks - returned_pks

    # Opinion: don't crash on missing — LLMs occasionally drop items.
    # Log and move on. You'll catch these on the next evaluate run anyway
    # because get_unevaluated_messages_for_user will still return them.
    if missing:
        print(f"[scoring] user={user.user_id} — LLM dropped {len(missing)} pks: {missing}")

    return [
        EvaluationDto(
            message_pk=s.message_pk,
            user_id=user.user_id,
            score=s.score,
            processed_at=now,
        )
        for s in scored.scores
        if s.message_pk in sent_pks   # silently discard any hallucinated pks
    ]


# ── Public interface ──────────────────────────────────────────────────────────

async def evaluate_messages(
    user: UserDto,
    messages: List[TelegramMessage],
) -> List[EvaluationDto]:
    """
    Splits messages into batches, scores each batch concurrently,
    returns flat list of EvaluationDto ready for batch_save_evaluations.
    """
    if not messages or not user.resume_text:
        return []

    batch_size = settings.SCORING_BATCH_SIZE  # default 10

    # slice into batches
    batches = [
        messages[i : i + batch_size]
        for i in range(0, len(messages), batch_size)
    ]

    # Opinion: don't fire 30 concurrent OpenAI calls blindly —
    # you'll hit rate limits fast. A semaphore lets you tune concurrency
    # without changing the gather pattern.
    sem = asyncio.Semaphore(settings.SCORING_MAX_CONCURRENT)  # e.g. 5

    async def _guarded(batch):
        async with sem:
            return await _score_batch(user, batch)

    results = await asyncio.gather(*[_guarded(b) for b in batches], return_exceptions=True)

    flat: List[EvaluationDto] = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Opinion: same principle — log and skip the failed batch.
            # The next evaluate run will retry those messages.
            print(f"[scoring] user={user.user_id} batch={i} failed: {res}")
        else:
            flat.extend(res)

    return flat