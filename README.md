# 🎯 Ammo Cost Log - Backend

Backend do aplikacji zarządzania strzelectwem z inteligentnym asystentem AI.

## ✨ Funkcjonalności

- **Zarządzanie sprzętem** - katalog broni i amunicji
- **Śledzenie kosztów** - sesje strzeleckie z automatycznym obliczaniem wydatków  
- **Analiza celności** - pomiar wyników z komentarzami AI (GPT-5-mini)
- **Statystyki** - miesięczne podsumowania i analizy

## 🛠️ Technologie

- FastAPI, SQLModel, SQLite, OpenAI API

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

Aplikacja używa GPT-5-mini do generowania komentarzy do sesji celnościowych. Użytkownik podaje własny klucz OpenAI w formularzu.

## 🚀 Deployment

Automatyczny deployment na Render.com przez `render.yaml`.

## 🔮 Plany na przyszłość

- Konta użytkowników z prywatnymi kolekcjami
- Poziomy zaawansowania (Początkujący, Średniozaawansowany, Zaawansowany)
- Inteligentne AI dostosowane do poziomu doświadczenia
