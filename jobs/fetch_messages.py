import asyncio
import datetime
from db.engine import get_session
from db.repos.messages import get_messages, batch_save_messages
from services.telegram_scraper import scrape_channel
from config import settings

async def run_fetch_job():
    with get_session() as session:
        latest = get_messages(session, limit=1, order_by_date_desc=True)
        date_from = latest[0].date if latest else datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    tasks = [
        scrape_channel(channel_id=ch, date_from=date_from)
        for ch in settings.telegram_channels
    ]
    results = await asyncio.gather(*tasks)
    messages = [msg for batch in results for msg in batch]

    with get_session() as session:
        inserted = batch_save_messages(messages, session)
    
    print(f"[fetch_job] inserted {inserted} new messages")
