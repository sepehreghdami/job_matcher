# services/scoring.py

import asyncio
from typing import List, Tuple
from pydantic import BaseModel
from agents import Agent, Runner
from schemas.telegram_message import TelegramMessage
from schemas.user import UserDto
from schemas.evaluation import EvaluationDto
from datetime import datetime, timezone
from config import settings


class MessageScore(BaseModel):
    message_pk: int
    score: float
    reason: str


class ScoringResult(BaseModel):
    scores: List[MessageScore]


INSTRUCTIONS = """
You are a senior technical recruiter with 15 years of experience matching 
candidates to roles across software engineering, data, and product.

Your task:
Given a candidate resume and a batch of job postings, score each posting 
on how well the candidate's background matches the role requirements.

Scoring rules:
- Score range: 1.0 to 10.0 (one decimal place)
- 1–3 : Poor match. Candidate lacks core required skills or the role is in a completely different domain.
- 4–6 : Partial match. Candidate meets some requirements but has clear gaps in either skills, seniority, or domain.
- 7–8 : Good match. Candidate meets most requirements. Minor gaps only.
- 9–10: Excellent match. Candidate exceeds or precisely fits the requirements.

Rules you must follow:
- Base your score ONLY on the resume and posting text provided.
- Do not infer or assume skills not mentioned in the resume.
- If a posting is not a job opportunity (spam, irrelevant), assign score 1.
- Each posting is labeled [1], [2], [3]... — return that exact number as message_pk.
- Do NOT use any other number found inside the posting text as message_pk.
- You MUST return a score for every posting — no skipping.
- The reason field must be one sentence explaining the key factor behind the score.
"""


def _build_user_prompt(
    resume: str,
    messages: List[TelegramMessage],
) -> Tuple[str, dict]:
    """
    Returns the prompt string and the index→pk mapping.
    We use sequential [1],[2],[3] labels so the LLM never sees real DB pks
    and can't confuse them with numbers inside the message text.
    """
    index_to_pk = {i + 1: msg.pk for i, msg in enumerate(messages)}

    postings = "\n\n".join(
        f"[{idx}]\n{(msg.text or '').strip()[:500]}"
        for idx, msg in zip(index_to_pk.keys(), messages)
    )

    prompt = f"""
CANDIDATE RESUME:
{resume.strip()}

JOB POSTINGS:
{postings}
"""
    return prompt, index_to_pk


_agent = Agent(
    name="job_opportunity_evaluator",
    model=settings.scoring_model,
    instructions=INSTRUCTIONS,
    output_type=ScoringResult,
)


async def _score_batch(
    user: UserDto,
    batch: List[TelegramMessage],
) -> List[EvaluationDto]:

    prompt, index_to_pk = _build_user_prompt(resume=user.resume_text, messages=batch)
    result = await Runner.run(_agent, prompt)
    scored: ScoringResult = result.final_output

    now = datetime.now(timezone.utc)

    sent_indices = set(index_to_pk.keys())           # {1, 2, 3, ...}
    returned_indices = {s.message_pk for s in scored.scores}
    missing = sent_indices - returned_indices

    if missing:
        print(f"[scoring] user={user.user_id} — LLM dropped indices {missing}")

    evals = []
    for s in scored.scores:
        real_pk = index_to_pk.get(s.message_pk)      # [1] → actual DB pk

        if real_pk is None:
            print(f"[scoring] user={user.user_id} — unknown index {s.message_pk}, skipping")
            continue

        evals.append(EvaluationDto(
            message_pk=real_pk,                       # ← real DB pk, not Telegram id
            user_id=user.user_id,
            score=s.score,
            processed_at=now,
        ))

    return evals


async def evaluate_messages(
    user: UserDto,
    messages: List[TelegramMessage],
) -> List[EvaluationDto]:
    if not messages or not user.resume_text:
        return []

    batch_size = settings.scoring_batch_size
    batches = [messages[i: i + batch_size] for i in range(0, len(messages), batch_size)]

    sem = asyncio.Semaphore(settings.scoring_max_concurrent)

    async def _guarded(batch):
        async with sem:
            return await _score_batch(user, batch)

    results = await asyncio.gather(*[_guarded(b) for b in batches], return_exceptions=True)

    flat: List[EvaluationDto] = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"[scoring] user={user.user_id} batch={i} failed: {res}")
        else:
            flat.extend(res)

    return flat