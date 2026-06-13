# # test_bot.py
# import asyncio
# from telegram import Bot
# from telegram.request import HTTPXRequest
# from config import settings

# async def main():

#     bot = Bot(token=settings.telegram_bot_token)

#     me = await bot.get_me()
#     print(f"Bot is alive: @{me.username}")

#     # paste YOUR numeric chat id here — get it from step 2 below
#     TEST_CHAT_ID = 1267322427
#     await bot.send_message(chat_id=TEST_CHAT_ID, text="test message")
#     print("Message sent successfully")

# asyncio.run(main())



from telethon import TelegramClient
import socks
from datetime import datetime
from config import settings
from schemas.telegram_message import TelegramMessage
from telethon_msg_to_model import telethon_msg_to_model
client = TelegramClient(
    "session_name",
    settings.telegram_api_id,
    settings.telegram_api_hash,
    # proxy=(socks.SOCKS5, "127.0.0.1", 10808),
    connection_retries=5,
    retry_delay=3,
)

async def scrape_channel(channel_username: str):
    channel = await client.get_entity(channel_username)
    messages = []
    async for msg in client.iter_messages(channel):

        messages.append(msg)

    return messages[0]

import asyncio

async def main():
    async with client:
        x = await scrape_channel("jobino_ai")
        print(x)

asyncio.run(main())
