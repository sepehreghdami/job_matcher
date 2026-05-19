# jobs/evaluate_job.py
import asyncio
from db.engine import get_session
from db.repos.users import get_users
from db.repos.messages import get_messages
from db.repos.evaluations import batch_save_evaluations
from services.scoring_service import evaluate_messages


async def run_evaluate_job():
    with get_session() as session:
        users = get_users(session, is_active=True)
        # only messages not yet evaluated — see note below
        messages = get_messages(session, has_text=True)

    # one coroutine per user — concurrent LLM calls
    tasks = [evaluate_for_user(user, messages) for user in users]
    all_evals = await asyncio.gather(*tasks)
    flat = [e for batch in all_evals for e in batch]

    with get_session() as session:
        batch_save_evaluations(flat, session, on_conflict="nothing")

async def evaluate_for_user(user, messages):

    return await evaluate_messages(user=user, messages=messages)