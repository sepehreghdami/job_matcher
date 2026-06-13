from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import  Mapped, mapped_column
from typing import Optional
from datetime import datetime
from db.base import Base



class TelegramMessageRow(Base):
    __tablename__ = "telegram_messages"
    __table_args__ = (
        UniqueConstraint("message_id", "channel_id", name="uq_msg_channel"),
    )

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
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







