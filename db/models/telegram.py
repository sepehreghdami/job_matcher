from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    create_engine,
    UniqueConstraint,
    text,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.exc import OperationalError
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from urllib.parse import urlparse
from schemas.telegram_message import MessageEntity,MediaInfo,Engagement,ForwardInfo,TelegramMessage


class Base(DeclarativeBase):
    pass



class TelegramMessageRow(Base):
    __tablename__ = "telegram_messages"
    __table_args__ = (
        UniqueConstraint("message_id", "channel_id", name="uq_msg_channel"),
    )

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    edit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    text: Mapped[Optional[str]] = mapped_column(Text)
    post_author: Mapped[Optional[str]] = mapped_column(String(255))
    grouped_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    
    entities: Mapped[Optional[dict]] = mapped_column(JSON)
    media: Mapped[Optional[dict]] = mapped_column(JSON)
    engagement: Mapped[Optional[dict]] = mapped_column(JSON)
    forward: Mapped[Optional[dict]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())




def create_db(database_url: str):
    """
    Create engine and ensure tables exist.
    If the database doesn't exist, it will be created automatically.
    """
    # Parse the database name from the URL
    # Example: postgresql+psycopg2://user:password@localhost:5432/telegram_scraper
    parsed = urlparse(database_url)
    db_name = parsed.path[1:]  # Remove leading slash
    db_url_without_db = f"{parsed.scheme}://{parsed.netloc}/postgres"
    
    # First, connect to default 'postgres' database to check if our DB exists
    engine_default = create_engine(db_url_without_db, echo=False)
    
    try:
        # Try to connect to the target database
        engine = create_engine(database_url, echo=False)
        engine.connect()
    except OperationalError as e:
        if f'database "{db_name}" does not exist' in str(e):
            # Create the database
            with engine_default.connect() as conn:
                conn.execute(text("COMMIT"))  # Required for CREATE DATABASE
                conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Database '{db_name}' created successfully.")
            # Now create engine for the newly created database
            engine = create_engine(database_url, echo=False)
        else:
            raise e
    finally:
        engine_default.dispose()
    
    # Create all tables
    Base.metadata.create_all(engine)
    return engine






