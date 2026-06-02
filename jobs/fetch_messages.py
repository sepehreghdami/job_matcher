from schemas.telegram_message import TelegramMessage

import asyncio
from datetime import datetime,timezone
from db.engine import get_session
from db.repos.messages import get_messages, batch_save_messages
from services.telegram_scraper import scrape_channel, start, stop
from config import settings


async def run_fetch_job():
    with get_session() as session:
        latest = get_messages(session, limit=1, order_by_date_desc=True)
        date_from = (
            latest[0].date
            if latest
            else datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        )

    print(f"messages last time fetched: {date_from}")

    await start()
    try:
        tasks = [scrape_channel(ch, date_from) for ch in settings.telegram_channels]
        results: list[list[TelegramMessage] | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )
    finally:
        await stop()

    messages: list[TelegramMessage] = []

    for ch, result in zip(settings.telegram_channels, results):
        if isinstance(result, Exception):
            print(f"[fetch_job] {ch} failed: {result}")
        else:
            messages.extend(result)

    with get_session() as session:
        inserted = batch_save_messages(messages, session)

    print(f"[fetch_job] inserted {inserted} new messages")
