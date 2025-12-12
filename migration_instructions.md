# Instrukcje migracji bazy danych

## Wymagania

- Python 3.8+
- Alembic zainstalowany (`pip install alembic`)
- Skonfigurowana zmienna środowiskowa `DATABASE_URL` (lub używa domyślnego SQLite `dev.db`)

## Pierwsza migracja

1. **Wygeneruj początkową migrację:**

```bash
cd ammo_cost_log-backend
alembic revision --autogenerate -m "Initial migration - remove expires_at from models"
```

2. **Przejrzyj wygenerowaną migrację:**

Sprawdź plik w `alembic/versions/` - upewnij się, że:
- Usuwa kolumny `expires_at` z tabel: `guns`, `ammo`, `maintenance`, `attachments`, `shooting_sessions`
- Zachowuje kolumny `expires_at` w tabelach: `users`, `user_settings`

3. **Zastosuj migrację:**

```bash
alembic upgrade head
```

## Aktualizacja istniejącej bazy danych

Jeśli masz już istniejącą bazę danych z danymi:

1. **Utwórz backup bazy danych** (ważne!)

2. **Uruchom migrację:**

```bash
alembic upgrade head
```

3. **Weryfikacja:**

Sprawdź czy kolumny `expires_at` zostały usunięte z odpowiednich tabel (oprócz `users` i `user_settings`).

## Cofanie migracji

Jeśli potrzebujesz cofnąć migrację:

```bash
alembic downgrade -1
```

## Tworzenie nowych migracji

Gdy wprowadzasz zmiany w modelach:

```bash
alembic revision --autogenerate -m "Opis zmian"
alembic upgrade head
```

## Uwagi

- Migracje są automatycznie wykrywane przez Alembic na podstawie zmian w modelach SQLModel
- W środowisku produkcyjnym zawsze testuj migracje na kopii bazy danych
- SQLite może mieć ograniczenia w niektórych operacjach migracji - dla produkcji zalecany jest PostgreSQL










