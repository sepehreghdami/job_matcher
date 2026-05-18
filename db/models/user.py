from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    Text,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Optional, List
from datetime import datetime
from schemas.user import UserDto


class Base(DeclarativeBase):
    pass
class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    resume_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)



