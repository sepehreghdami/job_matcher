# jobs/evaluate_job.py
import asyncio
from db.engine import get_session
from db.repos.user import get_users
from db.repos.messages import get_unevaluated_messages
from db.repos.evaluations import batch_save_evaluations
from services.scoring_service import evaluate_messages


async def run_evaluate_job():
    with get_session() as session:
        users = get_users(session, is_active=True)
        tasks = [evaluate_for_user(user, get_unevaluated_messages(session,user_id=user.user_id)) for user in users]
        await asyncio.gather(*tasks)




async def evaluate_for_user(user, messages, batch_size: int = 100):
    for i in range(0, len(messages), batch_size):
        batch = messages[i : i + batch_size]
        evals = await evaluate_messages(user=user, messages=batch)
        with get_session() as session:
            batch_save_evaluations(evals, session, on_conflict="nothing")
