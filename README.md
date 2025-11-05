# 🎯 Ammo Cost Log - Backend

Backend do aplikacji zarządzania strzelectwem z inteligentnym asystentem AI.

## ✨ Funkcjonalności

- **Zarządzanie sprzętem** - katalog broni i amunicji
- **Śledzenie kosztów** - sesje strzeleckie z automatycznym obliczaniem wydatków  
- **Analiza celności** - pomiar wyników z komentarzami AI (GPT-5-mini)
- **Statystyki** - miesięczne podsumowania i analizy

## 🛠️ Technologie

- FastAPI, SQLModel, PostgreSQL (Neon.tech), OpenAI API

## 📁 Struktura projektu

Projekt używa architektury warstwowej:

```
ammo_cost_log-backend/
├── main.py              
├── database.py         
├── models.py            
├── routers/             
│   ├── guns.py
│   ├── ammo.py
│   ├── sessions.py
│   └── auth.py
└── services/            
    ├── gun_service.py
    ├── ammo_service.py
    └── session_service.py  
```

**Architektura:**
- **Routers** - cienka warstwa HTTP, deleguje do serwisów
- **Services** - logika biznesowa (walidacja, kalkulacje, integracje)
- **Models** - modele danych i schematy Pydantic

## 🚀 Instalacja

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Dostęp**: http://localhost:8000

## 📡 API Endpoints

- `GET /api/guns/` - lista broni
- `POST /api/guns/` - dodaj broń
- `PUT /api/guns/{id}` - edytuj broń
- `DELETE /api/guns/{id}` - usuń broń
- `GET /api/ammo/` - lista amunicji
- `POST /api/ammo/` - dodaj amunicję
- `POST /api/sessions/cost` - dodaj sesję kosztową
- `POST /api/sessions/accuracy` - dodaj sesję celnościową
- `GET /api/sessions/` - lista sesji (kosztowe i celnościowe)
- `GET /api/sessions/summary` - statystyki miesięczne

## 🤖 AI Komentarze

Aplikacja używa GPT-5-mini do generowania komentarzy do sesji celnościowych. Użytkownik podaje własny klucz OpenAI w formularzu. Logika generowania komentarzy znajduje się w `services/session_service.py` (klasa `AIService`).

## 🧪 Testowanie

Dzięki separacji warstw, serwisy można testować niezależnie od FastAPI:

```python
from services.gun_service import GunService
from sqlmodel import Session

async def test_create_gun():
    gun = await GunService.create_gun(session, gun_data)
    assert gun.name == "Test"
```

## 🚀 Deployment

Automatyczny deployment na Render.com przez `render.yaml`.

### Konfiguracja bazy danych

Backend automatycznie wykrywa typ bazy danych na podstawie `DATABASE_URL`:
- Lokalnie: używa SQLite (`sqlite:///./dev.db`)
- Na Renderze: używa PostgreSQL z Neon.tech (connection string z dashboard Neon.tech)





## 📜 Changelog

Zobacz pełną historię zmian → [CHANGELOG.md](CHANGELOG.md)

## 🔮 Plany na przyszłość

- Konta użytkowników z prywatnymi kolekcjami
- Poziomy zaawansowania (Początkujący, Średniozaawansowany, Zaawansowany)
- Inteligentne AI dostosowane do poziomu doświadczenia
