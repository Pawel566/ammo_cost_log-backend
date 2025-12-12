-- Skrypt SQL do aktualizacji bazy danych
-- Dodaje kolumny group_cm i final_score do tabeli shooting_sessions

-- Dla SQLite:
-- ALTER TABLE shooting_sessions ADD COLUMN group_cm REAL;
-- ALTER TABLE shooting_sessions ADD COLUMN final_score REAL;

-- Dla PostgreSQL:
-- ALTER TABLE shooting_sessions ADD COLUMN IF NOT EXISTS group_cm FLOAT;
-- ALTER TABLE shooting_sessions ADD COLUMN IF NOT EXISTS final_score FLOAT;

-- Uruchom odpowiednie komendy w zależności od typu bazy danych

