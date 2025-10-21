# 🎯 Ammo Cost Log API

Aplikacja backendowa do śledzenia kosztów strzelania — stworzona w Python + FastAPI.  
Pozwala dodawać broń, amunicję oraz sesje strzeleckie z automatycznym liczeniem kosztów i podsumowaniem miesięcznym.

---

## 🧱 Stack technologiczny

| Warstwa | Technologia | Opis |
|----------|--------------|------|
| Backend | **Python + FastAPI** | główny framework aplikacji |
| ORM | **SQLModel** | modele danych i relacje |
| Baza danych | **SQLite / PostgreSQL (Supabase)** | lokalnie SQLite, na produkcji PostgreSQL |
| Deployment | **Render** | darmowy hosting backendu |
| Zarządzanie środowiskiem | `.env` + **python-dotenv** | dane konfiguracyjne i zmienne środowiskowe |

---

## 🚀 Funkcjonalności

- dodawanie / usuwanie broni (`/guns`)
- dodawanie / usuwanie amunicji (`/ammo`)
- rejestrowanie sesji strzeleckich (`/sessions`)
  - automatyczne liczenie kosztu (`shots × price_per_unit`)
  - walidacja daty i liczby strzałów
- podsumowanie kosztów miesięcznych (`/sessions/summary`)

---

## 🧩 Struktura projektu

```plaintext 
ammo_cost_log-backend/
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── main.py
├── database.py
├── models.py
│
├── routers/
│   ├── __init__.py
│   ├── guns.py
│   ├── ammo.py
│   └── sessions.py

```

---

## Instalacja zależności
pip install -r requirements.txt

---

## Uruchomienie serwera FastAPI
uvicorn main:app --reload

---


## Wersja 0.1

CRUD dla broni, amunicji i sesji

automatyczne liczenie kosztów

walidacja danych wejściowych

miesięczne podsumowanie kosztów