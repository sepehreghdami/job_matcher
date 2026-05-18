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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Optional, List
from datetime import datetime
from schemas.evaluation import EvaluationDto


class Base(DeclarativeBase):
    pass

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



def batch_save_evaluations(
    evaluations: List[EvaluationDto],
    session: Session,
    on_conflict: str = "nothing"
) -> int:
    """
    Batch insert/update message evaluations.
    
    Args:
        evaluations: List of EvaluationDto objects
        session: SQLAlchemy session
        on_conflict: "nothing" (ignore duplicates) or "update" (update score/timestamps)
    
    Returns:
        Number of rows inserted/updated
    
    Example:
        evals = [
            EvaluationDto(message_pk=1, user_id=123),
            EvaluationDto(message_pk=1, user_id=456, score=7.5, processed_at=datetime.now())
        ]
        batch_save_evaluations(evals, session)
    """
    if not evaluations:
        return 0
    
    eval_dicts = [e.model_dump(exclude={"id", "created_at"}, exclude_none=True) for e in evaluations]
    
    stmt = pg_insert(MessageEvaluation).values(eval_dicts)
    
    if on_conflict == "update":
        stmt = stmt.on_conflict_do_update(
            constraint="uq_eval_message_user",
            set_={
                "score": stmt.excluded.score,
                "processed_at": stmt.excluded.processed_at,
                "forwarded_at": stmt.excluded.forwarded_at,
            }
        )
    else:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_eval_message_user")
    
    result = session.execute(stmt)
    session.commit()
    return result.rowcount


def get_evaluations(
    session: Session,
    id: Optional[int] = None,
    message_pk: Optional[int] = None,
    user_id: Optional[int] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    is_processed: Optional[bool] = None,
    is_forwarded: Optional[bool] = None,
    limit: Optional[int] = None
) -> List[EvaluationDto]:
    """
    Get message evaluations with optional filters.
    
    Args:
        session: SQLAlchemy session
        id: Filter by evaluation id
        message_pk: Filter by message primary key
        user_id: Filter by user_id
        score_min: Minimum score (inclusive)
        score_max: Maximum score (inclusive)
        is_processed: True (processed), False (pending), None (all)
        is_forwarded: True (forwarded), False (not forwarded), None (all)
        limit: Maximum number of results
    
    Returns:
        List of EvaluationDto objects
    
    Examples:
        get_evaluations(session, is_processed=False)  # pending evaluations
        get_evaluations(session, score_min=5, is_forwarded=False)  # high scores not forwarded
        get_evaluations(session, user_id=123, is_processed=False)  # pending for specific user
    """
    query = session.query(MessageEvaluation)
    
    if id is not None:
        query = query.filter(MessageEvaluation.id == id)
    
    if message_pk is not None:
        query = query.filter(MessageEvaluation.message_pk == message_pk)
    
    if user_id is not None:
        query = query.filter(MessageEvaluation.user_id == user_id)
    
    if score_min is not None:
        query = query.filter(MessageEvaluation.score >= score_min)
    
    if score_max is not None:
        query = query.filter(MessageEvaluation.score <= score_max)
    
    if is_processed is True:
        query = query.filter(MessageEvaluation.processed_at.isnot(None))
    elif is_processed is False:
        query = query.filter(MessageEvaluation.processed_at.is_(None))
    
    if is_forwarded is True:
        query = query.filter(MessageEvaluation.forwarded_at.isnot(None))
    elif is_forwarded is False:
        query = query.filter(MessageEvaluation.forwarded_at.is_(None))
    
    if limit is not None:
        query = query.limit(limit)
    
    rows = query.all()
    return [EvaluationDto.model_validate(row) for row in rows]