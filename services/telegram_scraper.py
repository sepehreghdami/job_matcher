# services/telegram_scraper.py

from telethon import TelegramClient
from datetime import datetime
from config import settings
from schemas.telegram_message import TelegramMessage
from telethon_msg_to_model import telethon_msg_to_model

_client = None


def _get_client() -> TelegramClient:
    global _client
    if _client is None:
        _client = TelegramClient(
            "session_name",
            settings.telegram_api_id,
            settings.telegram_api_hash,
            connection_retries=5,
            retry_delay=3,
        )
    return _client


async def start():
    await _get_client().start()

async def stop():
    client = _get_client()
    await client.disconnect()

async def scrape_channel(channel_username: str, date_from: datetime) -> list[TelegramMessage]:
    client = _get_client()
    try:
        channel = await client.get_entity(channel_username)
    except Exception as e:
        print(f"Error: Could not access channel {channel_username}: {e}")
        return []

    messages = []
    async for msg in client.iter_messages(channel):
        if msg.date < date_from:
            break
        messages.append(telethon_msg_to_model(msg, channel_username))

    print(f"✓ {channel_username}: {len(messages)} messages")
    return messages