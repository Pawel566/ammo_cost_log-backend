# 🎯 Ammo Cost Log - Backend

Backend do aplikacji zarządzania strzelectwem z inteligentnym asystentem AI.

## ✨ Funkcjonalności

- **Zarządzanie sprzętem** - katalog broni i amunicji przypisany do użytkownika
- **Tryby użytkowników** - role guest/user/admin z izolacją danych i sesją gościa 24h
- **Walidacja danych** - schematy Pydantic w `schemas/` z ograniczeniami długości i wartości
- **Śledzenie kosztów** - sesje strzeleckie z automatycznym obliczaniem wydatków (koszt stały + cena amunicji × liczba strzałów)
- **Analiza celności** - pomiar wyników z komentarzami AI (`gpt-4o-mini`)
- **Statystyki** - miesięczne podsumowania i analizy (z paginacją `limit`/`offset`/`search`)
- **Uwierzytelnianie** - Supabase Auth z szczegółową obsługą błędów
- **UUID identyfikatory** - wszystkie zasoby korzystają z globalnie unikalnych ID

## 🛠️ Technologie

FastAPI, SQLModel, PostgreSQL (Neon.tech), OpenAI API, Supabase

## 🚀 Instalacja

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Dostęp**: http://localhost:8000

## 📡 API Endpoints

### Broń i Amunicja
- `GET /api/guns/` - lista broni (obsługuje `limit`, `offset`, `search`)
- `POST /api/guns/` - dodaj broń
- `PUT /api/guns/{id}` - edytuj broń
- `DELETE /api/guns/{id}` - usuń broń
- `GET /api/ammo/` - lista amunicji (obsługuje `limit`, `offset`, `search`)
- `POST /api/ammo/` - dodaj amunicję

### Sesje Strzeleckie
- `GET /api/shooting-sessions/` - lista sesji strzeleckich (obsługuje `limit`, `offset`, `search`, `gun_id`, `date_from`, `date_to`)
- `POST /api/shooting-sessions/` - dodaj sesję strzelecką (hybrydowa - może zawierać zarówno koszt jak i celność)
- `GET /api/shooting-sessions/{id}` - pobierz pojedynczą sesję
- `PATCH /api/shooting-sessions/{id}` - edytuj sesję (zachowuje koszt stały przy zmianie amunicji/liczby strzałów)
- `DELETE /api/shooting-sessions/{id}` - usuń sesję (automatycznie zwraca amunicję do magazynu)
- `GET /api/shooting-sessions/summary` - statystyki miesięczne (obsługuje `limit`, `offset`, `search`)

### Uwierzytelnianie i Konto
- `POST /api/auth/login` - logowanie
- `POST /api/auth/register` - rejestracja
- `GET /api/account/` - dane konta użytkownika

### Konserwacja i Wyposażenie
- `GET /api/maintenance/` - lista konserwacji
- `POST /api/maintenance/` - dodaj konserwację
- `GET /api/attachments/` - lista wyposażenia/akcesoriów
- `POST /api/attachments/` - dodaj wyposażenie

### Ustawienia
- `GET /api/settings/` - ustawienia użytkownika
- `PUT /api/settings/` - aktualizuj ustawienia

Żądania bez nagłówka `Authorization` otrzymują w odpowiedzi identyfikator `X-Guest-Session` oraz `X-Guest-Session-Expires-At`. Do kolejnych wywołań należy dołączać pierwszy nagłówek, aby utrzymać 24-godzinny sandbox gościa.

## 🤖 AI Komentarze

Aplikacja używa modelu `gpt-4o-mini` do generowania komentarzy do sesji celnościowych. Użytkownik podaje własny klucz OpenAI w formularzu, a backend obsługuje błędy i limity.

## 🚀 Deployment

Automatyczny deployment na Render.com przez `render.yaml`. Backend automatycznie wykrywa typ bazy danych na podstawie `DATABASE_URL` (SQLite lokalnie, PostgreSQL na produkcji).

## 🧪 Testy

```bash
pytest
```

Testy korzystają z wbudowanej bazy SQLite in-memory i pokrywają logikę serwisów broni, amunicji, sesji oraz generowania komentarzy AI.

## 🐳 Uruchomienie w Dockerze

```bash
docker compose up --build
```

Uruchamia kontenery `backend` (FastAPI na porcie 8000) i `db` (PostgreSQL 15 na porcie 5432). Zmienne środowiskowe można nadpisać w `.env` lub bezpośrednio przy starcie.

## ⚙️ Konfiguracja

Backend korzysta z `settings.py` (Pydantic Settings) i odczytuje zmienne środowiskowe z `.env`:

- `DATABASE_URL` – adres bazy danych (domyślnie `sqlite:///./dev.db`)
- `DEBUG` – włącza logowanie na poziomie `DEBUG`
- `SUPABASE_URL` – adres projektu Supabase
- `SUPABASE_ANON_KEY` – klucz anon Supabase
- `OPENAI_API_KEY` – opcjonalny klucz do komentarzy AI
- `GUEST_SESSION_TTL_HOURS` – czas życia danych gościa (domyślnie 24h)

Możesz utworzyć lokalny plik `.env` kopiując przykładowe wartości na potrzeby środowiska developerskiego.

## 📜 Changelog

Zobacz pełną historię zmian → [CHANGELOG.md](CHANGELOG.md)

## 🔮 Plany

- Moduł akcesoriów i dodatków do broni
- Harmonogramy konserwacji z przypomnieniami
- Rozszerzone raporty i porównania sesji
