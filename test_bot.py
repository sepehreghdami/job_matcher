# test_bot.py
import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest
from config import settings

async def main():

    bot = Bot(token=settings.telegram_bot_token)

    me = await bot.get_me()
    print(f"Bot is alive: @{me.username}")

    # paste YOUR numeric chat id here — get it from step 2 below
    TEST_CHAT_ID = 1267322427
    await bot.send_message(chat_id=TEST_CHAT_ID, text="test message")
    print("Message sent successfully")

asyncio.run(main())