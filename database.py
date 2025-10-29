from sqlmodel import SQLModel, create_engine, Session
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    DATABASE_URL, 
    echo=os.getenv("DEBUG", "false").lower() == "true",
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session