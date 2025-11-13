# 🎯 Ammo Cost Log - Backend

Backend do aplikacji zarządzania strzelectwem z inteligentnym asystentem AI.

## ✨ Funkcjonalności

- **Zarządzanie sprzętem** - katalog broni i amunicji przypisany do użytkownika
- **Tryby użytkowników** - role guest/user/admin z izolacją danych i sesją gościa 24h
- **Walidacja danych** - schematy Pydantic w `schemas/` z ograniczeniami długości i wartości
- **Śledzenie kosztów** - sesje strzeleckie z automatycznym obliczaniem wydatków
- **Analiza celności** - pomiar wyników z komentarzami AI (`gpt-4o-mini`)
- **Statystyki** - miesięczne podsumowania i analizy (z paginacją `limit`/`offset`/`search`)
- **Uwierzytelnianie** - Supabase Auth z szczegółową obsługą błędów

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

- `GET /api/guns/` - lista broni (obsługuje `limit`, `offset`, `search`)
- `POST /api/guns/` - dodaj broń
- `PUT /api/guns/{id}` - edytuj broń
- `DELETE /api/guns/{id}` - usuń broń
- `GET /api/ammo/` - lista amunicji (obsługuje `limit`, `offset`, `search`)
- `POST /api/ammo/` - dodaj amunicję
- `POST /api/sessions/cost` - dodaj sesję kosztową
- `POST /api/sessions/accuracy` - dodaj sesję celnościową
- `GET /api/sessions/` - lista sesji kosztowych i celnościowych (obsługuje `limit`, `offset`, `search`)
- `GET /api/sessions/summary` - statystyki miesięczne (obsługuje `limit`, `offset`, `search`)
- `POST /api/auth/login` - logowanie
- `POST /api/auth/register` - rejestracja

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
