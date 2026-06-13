# jobs/forward_job.py

import asyncio
from datetime import datetime, timezone
from db.engine import get_session
from db.repos.evaluations import get_evaluations, batch_save_evaluations
from db.repos.messages import get_messages
from db.repos.user import get_users
from schemas.evaluation import EvaluationDto
from services.forwarding_service import forward_message
from config import settings


async def run_forward_job():
    with get_session() as session:
        pending = get_evaluations(
            session,
            score_min=settings.forward_score_threshold,
            is_processed=True,
            is_forwarded=False,
        )

    if not pending:
        return

    with get_session() as session:
        message_pks = list({e.message_pk for e in pending})
        user_ids    = list({e.user_id    for e in pending})

        messages = get_messages(session, pks=message_pks)
        users    = get_users(session, user_ids=user_ids)

    message_map = {m.pk: m for m in messages}
    user_map    = {u.user_id: u for u in users}
    print(f"[forward] processing {len(pending)} evaluations")
    semaphore = asyncio.Semaphore(settings.forward_max_concurrent)
    tasks = [
        _forward_single(evaluation, message_map, user_map, semaphore)
        for evaluation in pending
    ]
    await asyncio.gather(*tasks)


async def _forward_single(
    evaluation: EvaluationDto,
    message_map: dict,
    user_map: dict,
    semaphore: asyncio.Semaphore,
):
    async with semaphore:
        message = message_map.get(evaluation.message_pk)
        user = user_map.get(evaluation.user_id)

        if not message:
            print(f"[forward] message pk={evaluation.message_pk} not found, skipping")
            return

        if not user or not user.telegram_username:
            print(f"[forward] user id={evaluation.user_id} has no telegram_username, skipping")
            return

        success = await forward_message(
            evaluation=evaluation,
            message=message,
            user=user,
        )

        if success == "ok":
            with get_session() as session:
                batch_save_evaluations(
                    [EvaluationDto(
                        id=evaluation.id,
                        message_pk=evaluation.message_pk,
                        user_id=evaluation.user_id,
                        score=evaluation.score,
                        processed_at=evaluation.processed_at,
                        forwarded_at=datetime.now(timezone.utc),
                    )],
                    session,
                    on_conflict="update",
                )