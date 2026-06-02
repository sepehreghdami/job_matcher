# db/engine.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from urllib.parse import urlparse
from config import settings
from db.base import Base
from db.models.user import User
from db.models.telegram import TelegramMessageRow
from db.models.message_evaluation import MessageEvaluation


def _ensure_database_exists(database_url: str):
    """Create the database if it doesn't exist yet."""
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/")
    postgres_url = f"{parsed.scheme}://{parsed.netloc}/postgres"

    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"[db] created database '{db_name}'")
    finally:
        engine.dispose()


def build_engine(database_url: str):
    _ensure_database_exists(database_url)
    engine = create_engine(
        database_url,
        pool_pre_ping=True,   # drops stale connections before using them
        echo=False,
    )
    Base.metadata.create_all(engine)  # no-op if tables already exist
    print("[db] tables verified")
    return engine


# module-level engine and session factory — created once on import
engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()