# Ammo Cost Log - Backend

Aplikacja do kompleksowego zarządzania strzelectwem sportowym i rekreacyjnym. Umożliwia śledzenie kosztów, analizę celności i zarządzanie sprzętem strzeleckim z inteligentnym asystentem AI.

## Cel aplikacji
Aplikacja służy do kompleksowego zarządzania strzelectwem sportowym i rekreacyjnym:

- **Zarządzanie sprzętem** - katalog broni i amunicji z cenami
- **Śledzenie kosztów** - rejestrowanie sesji strzeleckich z automatycznym obliczaniem wydatków
- **Analiza celności** - pomiar i ocena wyników strzeleckich
- **AI asystent** - inteligentne komentarze do sesji celnościowych (wymaga klucza API użytkownika)
- **Statystyki** - miesięczne podsumowania kosztów i postępów

## Technologie
- **FastAPI** - API framework
- **SQLModel** - ORM i walidacja danych
- **SQLite** - baza danych
- **OpenAI API** - komentarze AI

## Jak uruchomić

1. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

2. Uruchom serwer:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API będzie dostępne na: http://localhost:8000

**Uwaga**: AI komentarze wymagają klucza API OpenAI od użytkownika.

## Endpointy
- `GET /guns/` - lista broni
- `GET /ammo/` - lista amunicji  
- `POST /sessions/cost` - dodaj sesję kosztową
- `POST /sessions/accuracy` - dodaj sesję celnościową
- `GET /sessions/summary` - statystyki miesięczne

## Plany na przyszłość
- **Migracja do Supabase** - przejście z SQLite na Supabase 
- **Konta użytkowników** - logowanie i rejestracja, każdy użytkownik ma dostęp tylko do swoich danych
- **Poziomy zaawansowania** - wybór poziomu (Początkujący, Średniozaawansowany, Zaawansowany)
- **Inteligentne AI** - model AI dostosowuje rygorystyczność oceny do poziomu doświadczenia użytkownika
