from telethon import TelegramClient
import socks
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
from config import settings

from telegram_message import TelegramMessage
from telethon_msg_to_model import telethon_msg_to_model


API_ID = settings.telegram_api_id
API_HASH = settings.telegram_api_hash
CHANNELS = settings.telegram_channels

client = TelegramClient(
    "session_name",
    API_ID,
    API_HASH,
    proxy=(socks.SOCKS5, "127.0.0.1", 10808),
    connection_retries=5,
    retry_delay=3,
)


async def fetch_channel_messages(channel_username: str, from_date: datetime) -> list[TelegramMessage]:
    """Fetch today's messages from a single channel."""
    try:
        channel = await client.get_entity(channel_username)
    except Exception as e:
        print(f"Error: Could not access channel {channel_username}")
        print(e)
        return []

    print(f"Fetching messages from: {channel_username}")

    messages = []
    async for msg in client.iter_messages(channel):
        if msg.date < from_date:
            break
        messages.append(telethon_msg_to_model(msg))

    print(f"✓ {channel_username}: {len(messages)} messages")
    return messages


async def extract_messages(from_date: datetime):
    """Fetch messages from all channels concurrently."""
    print("Connecting to Telegram...")

    # Fetch all channels concurrently
    tasks = [fetch_channel_messages(ch) for ch in CHANNELS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results and filter out errors
    all_messages = []
    for result in results:
        if isinstance(result, list):
            all_messages.extend(result)
        else:
            print(f"Task failed: {result}")

    if all_messages:
        print(f"\nTotal messages: {len(all_messages)}")
        # print(all_messages[0])

    return all_messages
