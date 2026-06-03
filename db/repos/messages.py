from db.models.telegram import TelegramMessageRow
from db.models.message_evaluation import MessageEvaluation
from sqlalchemy.orm import  Session
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from schemas.telegram_message import MessageEntity,MediaInfo,Engagement,ForwardInfo,TelegramMessage
from sqlalchemy import select




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
        pk=row.pk,            
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
    pks: Optional[List[int]] = None,
    message_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    has_text: Optional[bool] = None,
    limit: Optional[int] = None,
    order_by_date_desc: bool = False
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
        order_by_date_desc: Order by date descending (newest first)
    
    Returns:
        List of TelegramMessage objects
    
    Examples:
        get_messages(session, channel_id=123)
        get_messages(session, date_from=datetime(2025, 1, 1), has_text=True)
        get_messages(session, channel_id=123, order_by_date_desc=True)
    """
    query = session.query(TelegramMessageRow)
    
    if pks is not None:
        query = query.filter(TelegramMessageRow.pk.in_(pks))
    
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
    
    if order_by_date_desc:
        query = query.order_by(TelegramMessageRow.date.desc())
    
    if limit is not None:
        query = query.limit(limit)
    
    rows = query.all()
    return [_from_row(row) for row in rows]


    
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



def get_unevaluated_messages(session: Session, user_id: int) -> list[TelegramMessageRow]:
    evaluated = (
        select(MessageEvaluation.message_pk)
        .where(MessageEvaluation.user_id == user_id)
        .subquery()
    )

    stmt = (
        select(TelegramMessageRow)
        .outerjoin(evaluated, TelegramMessageRow.pk == evaluated.c.message_pk)
        .where(evaluated.c.message_pk == None) 
    )

    return session.scalars(stmt).all()