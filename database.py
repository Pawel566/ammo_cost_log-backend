from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from settings import settings

DATABASE_URL = settings.database_url or "sqlite:///./dev.db"

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

echo_sql = settings.debug

engine = create_engine(
    DATABASE_URL,
    echo=echo_sql,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def get_async_session() -> Generator[Session, None, None]:
    """Unified function for getting database session"""
    with Session(engine) as session:
        yield session

def init_db():
    pass

def get_session() -> Generator[Session, None, None]:
    """Alias for get_async_session for backward compatibility"""
    with Session(engine) as session:
        yield session