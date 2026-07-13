# jobs/extract_keywords.py
"""
Backfill job: finds active users who have a resume but no extracted keywords
yet (new signups whose synchronous extraction failed, or legacy users from
before this feature shipped) and extracts + saves keywords for them.

New signups get keywords synchronously at /start or /updatecv already
(services/bot_handler.py) — this job is the retry/safety net, run on an
interval (settings.keyword_extraction_interval_minutes).
"""

import asyncio
import logging
from db.engine import get_session
from db.repos.user import get_users, batch_save_users
from schemas.user import UserDto
from services.keyword_service import extract_keywords
from config import settings

logger = logging.getLogger(__name__)


async def run_keyword_extraction_job():
    logger.info("[keyword_extraction_job] starting")

    with get_session() as session:
        users = get_users(session, is_active=True, has_keywords=False)

    users = [u for u in users if u.resume_text]  # defensive; should always be true

    if not users:
        logger.info("[keyword_extraction_job] nothing to backfill")
        return

    logger.info("[keyword_extraction_job] backfilling keywords for %d users", len(users))

    sem = asyncio.Semaphore(settings.scoring_max_concurrent)  # reuse — same LLM endpoint/rate limits

    async def _extract_and_save(user: UserDto) -> int:
        async with sem:
            keywords = await extract_keywords(user.resume_text)
            with get_session() as session:
                batch_save_users(
                    [UserDto(
                        telegram_chat_id=user.telegram_chat_id,
                        telegram_username=user.telegram_username,
                        resume_text=user.resume_text,
                        is_active=user.is_active,
                        keywords=keywords or None,
                    )],
                    session,
                    on_conflict="update",
                )
            return len(keywords)

    results = await asyncio.gather(*(_extract_and_save(u) for u in users), return_exceptions=True)

    ok = 0
    for user, res in zip(users, results):
        if isinstance(res, Exception):
            logger.error("[keyword_extraction_job] user=%s failed: %s", user.user_id, res)
        else:
            ok += 1

    logger.info("[keyword_extraction_job] report: %d/%d users backfilled with keywords", ok, len(users))
