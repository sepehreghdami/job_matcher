from schemas.telegram_message import TelegramMessage

import asyncio
import logging
from datetime import datetime,timezone
from db.engine import get_session
from db.repos.messages import get_messages, batch_save_messages
from services.telegram_scraper import scrape_channel, start, stop
from config import settings

logger = logging.getLogger(__name__)


async def run_fetch_job():
    logger.info("[fetch_job] starting")

    with get_session() as session:
        latest = get_messages(session, limit=1, order_by_date_desc=True)
        date_from = (
            latest[0].date
            if latest
            else datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        )

    logger.info("[fetch_job] fetching messages since %s across %d channels", date_from, len(settings.telegram_channels))

    await start()
    try:
        tasks = [scrape_channel(ch, date_from) for ch in settings.telegram_channels]
        results: list[list[TelegramMessage] | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )
    finally:
        await stop()

    messages: list[TelegramMessage] = []
    failed_channels = 0

    for ch, result in zip(settings.telegram_channels, results):
        if isinstance(result, Exception):
            failed_channels += 1
            logger.error("[fetch_job] channel %s failed: %s", ch, result)
        else:
            messages.extend(result)

    with get_session() as session:
        inserted = batch_save_messages(messages, session)

    logger.info(
        "[fetch_job] report: %d channels scraped, %d failed, %d messages scraped, %d new messages inserted",
        len(settings.telegram_channels) - failed_channels,
        failed_channels,
        len(messages),
        inserted,
    )
