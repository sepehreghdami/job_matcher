# services/telegram_scraper.py

import logging
from telethon import TelegramClient
from datetime import datetime
from config import settings
from schemas.telegram_message import TelegramMessage
from telethon_msg_to_model import telethon_msg_to_model
from services.proxy import get_telethon_proxy

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> TelegramClient:
    global _client
    if _client is None:
        proxy = get_telethon_proxy()
        logger.info("Creating Telethon client (proxy=%s)", "enabled" if proxy else "direct")
        _client = TelegramClient(
            "session_name",
            settings.telegram_api_id,
            settings.telegram_api_hash,
            connection_retries=5,
            retry_delay=3,
            proxy=proxy,  # None = direct connection
        )
    return _client


async def start():
    logger.info("Connecting Telethon client")
    await _get_client().start()
    logger.info("Telethon client connected")

async def stop():
    client = _get_client()
    await client.disconnect()
    logger.info("Telethon client disconnected")

async def scrape_channel(channel_username: str, date_from: datetime) -> list[TelegramMessage]:
    logger.debug("Scraping channel %s (since %s)", channel_username, date_from)
    client = _get_client()
    try:
        channel = await client.get_entity(channel_username)
    except Exception as e:
        logger.error("Could not access channel %s: %s", channel_username, e)
        return []

    messages = []
    async for msg in client.iter_messages(channel):
        if msg.date < date_from:
            break
        messages.append(telethon_msg_to_model(msg, channel_username))

    logger.info("Scraped %s: %d messages", channel_username, len(messages))
    return messages