# Changelog

## [0.3.0] – 2025-11-13
### Dodano
- Role użytkowników (guest, user, admin) oraz automatyczne sesje gościa
- Tymczasowe dane sandbox z limitem ważności dla użytkowników gości
- Pydanticowe schematy `schemas/` (`Gun`, `Ammo`, `Session`) z walidacją wejścia
- Paginacja `limit`/`offset`/`search` dla endpointów listujących
- Centralny plik `settings.py` do zarządzania zmiennymi środowiskowymi
- Dockerfile, docker-compose (PostgreSQL) i .dockerignore dla powtarzalnego uruchamiania
- Katalog `tests/` z testami jednostkowymi (Gun, Ammo, Sessions, AI comment)

### Zmieniono
- Modele danych przechowują `user_id` i `expires_at`, zapewniając separację danych
- Serwisy i routery filtrują operacje według użytkownika oraz przedłużają ważność danych gościa
- Endpointy listujące zwracają strukturę `{ "total": ..., "items": [...] }`
- Logowanie i konfiguracja połączeń korzystają z ustawień środowiskowych


## [0.2.0] – 2025-11-05
### Dodano
- Warstwa serwisowa (`services/`) – logika przeniesiona z routerów
- Obsługa błędów Supabase i OpenAI z szczegółowymi komunikatami


### Zmieniono
- Poprawiono strukturę projektu (routery = routing, serwisy = logika)
- Ulepszona obsługa wyjątków



