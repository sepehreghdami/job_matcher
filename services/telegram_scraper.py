# services/telegram_scraper.py

from telethon import TelegramClient
import socks
from datetime import datetime
from config import settings
from schemas.telegram_message import TelegramMessage
from telethon_msg_to_model import telethon_msg_to_model

# module-level client — created once, started/stopped by main.py
client = TelegramClient(
    "session_name",
    settings.telegram_api_id,
    settings.telegram_api_hash,
    proxy=(socks.SOCKS5, "127.0.0.1", 10808),
    connection_retries=5,
    retry_delay=3,
)

async def start():
    await client.start()

async def stop():
    await client.disconnect()

async def scrape_channel(channel_username: str, date_from: datetime) -> list[TelegramMessage]:
    try:
        channel = await client.get_entity(channel_username)
    except Exception as e:
        print(f"Error: Could not access channel {channel_username}: {e}")
        return []

    messages = []
    async for msg in client.iter_messages(channel):
        if msg.date < date_from:
            break
        messages.append(telethon_msg_to_model(msg))

    print(f"✓ {channel_username}: {len(messages)} messages")
    return messages