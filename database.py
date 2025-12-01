from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from settings import settings
from sqlalchemy import inspect, text
import logging

DATABASE_URL = settings.database_url or "sqlite:///./dev.db"

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

echo_sql = settings.debug

engine = create_engine(
    DATABASE_URL,
    echo=echo_sql,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def init_db():
    SQLModel.metadata.create_all(engine)
    
    try:
        inspector = inspect(engine)
        if inspector.has_table("user_settings"):
            columns = [col["name"] for col in inspector.get_columns("user_settings")]
            if "language" not in columns:
                with engine.begin() as conn:
                    if "sqlite" in DATABASE_URL:
                        conn.execute(text("ALTER TABLE user_settings ADD COLUMN language VARCHAR(10) DEFAULT 'pl'"))
                    else:
                        conn.execute(text("ALTER TABLE user_settings ADD COLUMN language VARCHAR(10) DEFAULT 'pl'"))
    except Exception as e:
        logging.warning(f"Could not add language column to user_settings: {e}")

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session