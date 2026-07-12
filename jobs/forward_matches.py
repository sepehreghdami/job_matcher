# jobs/forward_job.py

import asyncio
import logging
from datetime import datetime, timezone
from db.engine import get_session
from db.repos.evaluations import get_evaluations, batch_save_evaluations
from db.repos.messages import get_messages
from db.repos.user import get_users
from schemas.evaluation import EvaluationDto
from services.forwarding_service import forward_message
from config import settings

logger = logging.getLogger(__name__)


async def run_forward_job():
    logger.info("[forward_job] starting")

    with get_session() as session:
        pending = get_evaluations(
            session,
            score_min=settings.forward_score_threshold,
            is_processed=True,
            is_forwarded=False,
        )

    if not pending:
        logger.info("[forward_job] nothing to forward")
        return

    with get_session() as session:
        message_pks = list({e.message_pk for e in pending})
        user_ids    = list({e.user_id    for e in pending})

        messages = get_messages(session, pks=message_pks)
        users    = get_users(session, user_ids=user_ids)

    message_map = {m.pk: m for m in messages}
    user_map    = {u.user_id: u for u in users}
    logger.info("[forward_job] processing %d evaluations for %d users", len(pending), len(user_ids))
    semaphore = asyncio.Semaphore(settings.forward_max_concurrent)
    tasks = [
        _forward_single(evaluation, message_map, user_map, semaphore)
        for evaluation in pending
    ]
    results = await asyncio.gather(*tasks)

    counts = {"ok": 0, "permanent_failure": 0, "transient_failure": 0, "skipped": 0}
    for status in results:
        counts[status] = counts.get(status, 0) + 1

    logger.info(
        "[forward_job] report: %d sent, %d permanent failures, %d transient (will retry), %d skipped",
        counts["ok"], counts["permanent_failure"], counts["transient_failure"], counts["skipped"],
    )


async def _forward_single(
    evaluation: EvaluationDto,
    message_map: dict,
    user_map: dict,
    semaphore: asyncio.Semaphore,
) -> str:
    async with semaphore:
        message = message_map.get(evaluation.message_pk)
        user = user_map.get(evaluation.user_id)

        if not message:
            logger.warning("[forward_job] message pk=%s not found, skipping", evaluation.message_pk)
            return "skipped"

        if not user or not user.telegram_username:
            logger.warning("[forward_job] user id=%s has no telegram_username, skipping", evaluation.user_id)
            return "skipped"

        status = await forward_message(
            evaluation=evaluation,
            message=message,
            user=user,
        )

        if status in ("ok", "permanent_failure"):
            now = datetime.now(timezone.utc)
            with get_session() as session:
                batch_save_evaluations(
                    [evaluation.model_copy(update={"forwarded_at": now})],
                    session,
                    on_conflict="update",
                )
        else:
            logger.warning("[forward_job] transient failure for eval id=%s, will retry", evaluation.id)

        return status