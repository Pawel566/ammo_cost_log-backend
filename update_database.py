#!/usr/bin/env python3
"""
Skrypt do aktualizacji bazy danych - dodaje kolumny group_cm i final_score do shooting_sessions
"""
import sys
import os

# Dodaj ścieżkę projektu
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, engine
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)

def update_database():
    """Aktualizuje bazę danych dodając brakujące kolumny"""
    print("Inicjalizacja bazy danych...")
    init_db()
    
    print("Sprawdzanie kolumn w shooting_sessions...")
    inspector = inspect(engine)
    
    if not inspector.has_table("shooting_sessions"):
        print("Tabela shooting_sessions nie istnieje. Zostanie utworzona przy następnym uruchomieniu aplikacji.")
        return
    
    columns = [col["name"] for col in inspector.get_columns("shooting_sessions")]
    print(f"Obecne kolumny: {', '.join(columns)}")
    
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    added = False
    
    if "group_cm" not in columns:
        try:
            with engine.begin() as conn:
                if "sqlite" in DATABASE_URL:
                    conn.execute(text("ALTER TABLE shooting_sessions ADD COLUMN group_cm REAL"))
                else:
                    conn.execute(text("ALTER TABLE shooting_sessions ADD COLUMN group_cm FLOAT"))
            print("✓ Dodano kolumnę group_cm")
            added = True
        except Exception as e:
            print(f"✗ Błąd podczas dodawania group_cm: {e}")
    else:
        print("✓ Kolumna group_cm już istnieje")
    
    if "final_score" not in columns:
        try:
            with engine.begin() as conn:
                if "sqlite" in DATABASE_URL:
                    conn.execute(text("ALTER TABLE shooting_sessions ADD COLUMN final_score REAL"))
                else:
                    conn.execute(text("ALTER TABLE shooting_sessions ADD COLUMN final_score FLOAT"))
            print("✓ Dodano kolumnę final_score")
            added = True
        except Exception as e:
            print(f"✗ Błąd podczas dodawania final_score: {e}")
    else:
        print("✓ Kolumna final_score już istnieje")
    
    if not added:
        print("\nWszystkie kolumny są już obecne w bazie danych.")
    else:
        print("\nBaza danych została zaktualizowana pomyślnie!")

if __name__ == "__main__":
    update_database()

