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

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session