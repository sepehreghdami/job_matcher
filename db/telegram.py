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
from telegram_message import TelegramMessage
from sqlalchemy.exc import OperationalError
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from urllib.parse import urlparse
from telegram_message import MessageEntity,MediaInfo,Engagement,ForwardInfo


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


def _to_row(msg: TelegramMessage) -> dict:
    return {
        "message_id": msg.id,
        "channel_id": msg.channel_id,
        "date": msg.date,
        "edit_date": msg.edit_date,
        "text": msg.text,
        "post_author": msg.post_author,
        "grouped_id": msg.grouped_id,
        "entities": [e.model_dump(mode="json") for e in msg.entities] or None,
        "media": msg.media.model_dump(mode="json") if msg.media else None,
        "engagement": msg.engagement.model_dump(mode="json") if msg.engagement else None,
        "forward": msg.forward.model_dump(mode="json") if msg.forward else None,
    }




def batch_save_messages(
    messages: List[TelegramMessage],
    session: Session,
) -> int:
    """
    Insert a list of TelegramMessage objects into Postgres.
    Duplicates (same message_id + channel_id) are silently ignored.

    Returns the number of rows actually inserted.
    """
    if not messages:
        return 0


    rows = [_to_row(m) for m in messages]

    stmt = (
        pg_insert(TelegramMessageRow)
        .values(rows)
        .on_conflict_do_nothing(constraint="uq_msg_channel")
    )

    result = session.execute(stmt)
    session.commit()
    return result.rowcount  # rows actually written (duplicates excluded)



def _from_row(row: TelegramMessageRow) -> TelegramMessage:
    return TelegramMessage(
        id=row.message_id,
        channel_id=row.channel_id,
        date=row.date,
        edit_date=row.edit_date,
        text=row.text,
        entities=[MessageEntity(**e) for e in (row.entities or [])],
        media=MediaInfo(**row.media) if row.media else None,
        engagement=Engagement(**row.engagement) if row.engagement else None,
        post_author=row.post_author,
        grouped_id=row.grouped_id,
        forward=ForwardInfo(**row.forward) if row.forward else None,
    )

def get_messages(
    session: Session,
    pk: Optional[int] = None,
    message_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    has_text: Optional[bool] = None,
    limit: Optional[int] = None
) -> List[TelegramMessage]:
    """
    Get messages with optional filters.
    
    Args:
        session: SQLAlchemy session
        pk: Filter by primary key
        message_id: Filter by message_id
        channel_id: Filter by channel_id
        date_from: Messages after this date
        date_to: Messages before this date
        has_text: True (only with text), False (only without text), None (all)
        limit: Maximum number of results
    
    Returns:
        List of TelegramMessage objects
    
    Examples:
        get_messages(session, channel_id=123)
        get_messages(session, date_from=datetime(2025, 1, 1), has_text=True)
    """
    query = session.query(TelegramMessageRow)
    
    if pk is not None:
        query = query.filter(TelegramMessageRow.pk == pk)
    
    if message_id is not None:
        query = query.filter(TelegramMessageRow.message_id == message_id)
    
    if channel_id is not None:
        query = query.filter(TelegramMessageRow.channel_id == channel_id)
    
    if date_from is not None:
        query = query.filter(TelegramMessageRow.date >= date_from)
    
    if date_to is not None:
        query = query.filter(TelegramMessageRow.date <= date_to)
    
    if has_text is True:
        query = query.filter(TelegramMessageRow.text.isnot(None))
    elif has_text is False:
        query = query.filter(TelegramMessageRow.text.is_(None))
    
    if limit is not None:
        query = query.limit(limit)
    
    rows = query.all()
    return [_from_row(row) for row in rows]