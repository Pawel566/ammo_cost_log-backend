from sqlmodel import SQLModel, create_engine, Session
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

engine = create_engine(
    DATABASE_URL, 
    echo=os.getenv("DEBUG", "false").lower() == "true",
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def init_db():
    """Inicjalizuje bazę danych i tworzy wszystkie tabele"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency do uzyskiwania sesji bazy danych"""
    with Session(engine) as session:
        yield session