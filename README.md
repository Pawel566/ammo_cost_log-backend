# Ammo Cost Log - Backend

Aplikacja do śledzenia kosztów i celności strzeleckich.

## Co robi
- Zarządzanie bronią i amunicją
- Rejestrowanie sesji kosztowych i celnościowych
- Automatyczne obliczanie kosztów i celności
- AI komentarze do sesji celnościowych (wymaga klucza API użytkownika)
- Statystyki miesięczne

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
- **Konta użytkowników** - logowanie i rejestracja, każdy użytkownik ma dostęp tylko do swoich danych
- **Poziomy zaawansowania** - wybór poziomu (Początkujący, Średniozaawansowany, Zaawansowany)
- **Inteligentne AI** - model AI dostosowuje rygorystyczność oceny do poziomu doświadczenia użytkownika