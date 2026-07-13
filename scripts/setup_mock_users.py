# scripts/setup_mock_users.py
"""
One-off setup for the 20-user keyword-filter recall experiment.

Inserts the 20 mock resumes (scripts/mock_resumes.py) as INACTIVE users
(is_active=False) with fake telegram_chat_ids in the 900001-900020 range, so
the live production scheduler (which only ever queries is_active=True users)
never picks them up. Then extracts real keywords for each via the real LLM
(services/keyword_service.py) — this is the only real-cost step here, ~20
cheap calls.

Usage:
    source env-scrapper/bin/activate
    python -m scripts.setup_mock_users
"""

import asyncio
import logging

from logging_config import setup_logging

setup_logging()

from sqlalchemy import select
from db.engine import get_session
from db.repos.user import batch_save_users
from db.models.user import User
from schemas.user import UserDto
from services.keyword_service import extract_keywords
from scripts.mock_resumes import MOCK_RESUMES

logger = logging.getLogger(__name__)

MOCK_CHAT_ID_BASE = 900000  # 900001..900020


async def main():
    users = [
        UserDto(
            telegram_chat_id=MOCK_CHAT_ID_BASE + i,
            telegram_username=f"mock_user_{i:02d}",
            resume_text=entry["resume"].strip(),
            is_active=False,  # never picked up by the live scheduler
        )
        for i, entry in enumerate(MOCK_RESUMES, start=1)
    ]

    with get_session() as session:
        inserted = batch_save_users(users, session, on_conflict="update")
    logger.info("[mock_setup] inserted/updated %d mock users", inserted)

    mock_chat_ids = [MOCK_CHAT_ID_BASE + i for i in range(1, 21)]
    with get_session() as session:
        rows = session.execute(
            select(User).where(User.telegram_chat_id.in_(mock_chat_ids)).order_by(User.telegram_chat_id)
        ).scalars().all()
        mock_users = [UserDto.model_validate(r) for r in rows]

    logger.info("[mock_setup] extracting keywords for %d mock users", len(mock_users))

    for idx, user in enumerate(mock_users, start=1):
        keywords = await extract_keywords(user.resume_text)
        with get_session() as session:
            batch_save_users(
                [UserDto(
                    telegram_chat_id=user.telegram_chat_id,
                    telegram_username=user.telegram_username,
                    resume_text=user.resume_text,
                    is_active=False,
                    keywords=keywords or None,
                )],
                session,
                on_conflict="update",
            )
        name = MOCK_RESUMES[idx - 1]["name"]
        logger.info("[mock_setup] (%d/20) %s -> %d keywords: %s", idx, name, len(keywords), keywords)

    logger.info("[mock_setup] done")


if __name__ == "__main__":
    asyncio.run(main())
