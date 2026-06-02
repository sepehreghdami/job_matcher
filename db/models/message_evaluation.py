from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from db.base import Base


class MessageEvaluation(Base):
    """
    Tracks LLM scoring of messages against user resumes.
    One row per (message, user) pair.
    """
    __tablename__ = "message_evaluations"
    __table_args__ = (
        UniqueConstraint("message_pk", "user_id", name="uq_eval_message_user"),
        Index("ix_eval_unprocessed", "user_id", "processed_at"),  # fetch pending evaluations per user
        Index("ix_eval_high_score", "score", "forwarded_at"),  # find high-scoring unfrozen messages
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_pk: Mapped[int] = mapped_column(Integer, ForeignKey("telegram_messages.pk", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    score: Mapped[Optional[float]] = mapped_column(Float)  # 0-10, null if not yet processed
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # null = pending
    forwarded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # null = not forwarded yet
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



