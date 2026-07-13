from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    JSON,
    String,
    Text,
    func
)
from sqlalchemy.orm import  Mapped, mapped_column
from typing import Optional
from datetime import datetime
from db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, index=True)  # ← Mapped[Optional[int]]
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    resume_text: Mapped[Optional[str]] = mapped_column(Text)
    # none_as_null=True: without it, SQLAlchemy's JSON type serializes Python
    # None as the JSON literal `null` (a real, non-NULL value) instead of SQL
    # NULL, which silently breaks `.is_(None)`/`.isnot(None)` filters (e.g.
    # get_users(has_keywords=...)).
    keywords: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)



