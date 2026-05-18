from extract_todays_messages import client, extract_messages
from db.telegram import create_db, batch_save_messages
from sqlalchemy.orm import sessionmaker
import asyncio
from config import settings



DATABASE_URL = settings.database_url


engine = create_db(DATABASE_URL)  
SessionLocal = sessionmaker(bind=engine)

async def main():
    async with client:

        
        messages = extract_messages()

    with SessionLocal() as session:
        inserted = batch_save_messages(messages, session)
        print(f"Saved {inserted} new messages to DB.")



if __name__ == "__main__":
    asyncio.run(main())

