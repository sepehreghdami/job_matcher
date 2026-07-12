# jobs/evaluate_job.py
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from db.engine import get_session
from db.repos.user import get_users
from db.repos.messages import get_unevaluated_messages
from db.repos.evaluations import batch_save_evaluations
from services.scoring_service import evaluate_messages

logger = logging.getLogger(__name__)


async def run_evaluate_job():
    logger.info("[evaluate_job] starting")

    date_from = datetime.now(timezone.utc) - timedelta(days=7)
    with get_session() as session:
        users = get_users(session, is_active=True)
        user_messages = {
            user.user_id: get_unevaluated_messages(session, user_id=user.user_id, date_from=date_from)
            for user in users
        }

    logger.info(
        "[evaluate_job] evaluating %d active users, %d unevaluated messages total",
        len(users), sum(len(m) for m in user_messages.values()),
    )

    tasks = [evaluate_for_user(user, user_messages[user.user_id]) for user in users]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    saved_total = 0
    failed_users = 0
    for user, res in zip(users, results):
        if isinstance(res, Exception):
            failed_users += 1
            logger.error("[evaluate_job] user=%s failed: %s", user.user_id, res)
        else:
            saved_total += res

    logger.info(
        "[evaluate_job] report: %d/%d users ok, %d evaluations saved",
        len(users) - failed_users, len(users), saved_total,
    )


async def evaluate_for_user(user, messages, batch_size: int = 100) -> int:
    if not messages:
        return 0

    saved = 0
    for i in range(0, len(messages), batch_size):
        batch = messages[i : i + batch_size]
        evals = await evaluate_messages(user=user, messages=batch)
        with get_session() as session:
            batch_save_evaluations(evals, session, on_conflict="nothing")
        saved += len(evals)

    logger.info("[evaluate_job] user=%s: %d messages processed, %d evaluations saved", user.user_id, len(messages), saved)
    return saved
