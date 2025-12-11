# Changelog

## [0.6.8] – 2025-12-11
### Dodano
- Ikony rang dla pierwszych 6 poziomów (Nowicjusz, Adepciak, Stabilny Strzelec, Celny Strzelec, Precyzyjny Strzelec, Zaawansowany Strzelec)
- Walidacja wartości dla pól `precision_help`, `recoil_reduction`, `ergonomics` w dodatkach (dozwolone: none, low, medium, high)
- Walidacja daty w przyszłości dla sesji strzeleckich i daty utworzenia broni
- Walidacja maksymalnych wartości dla pól numerycznych (ceny, ilości, strzały, odległości, grupy)

### Zmieniono
- Zmieniono "jakość sesji" na "punktacja końcowa" w interfejsie
- Ujednolicono `min_length` dla nazw broni i amunicji (schema i model: 2 znaki)
- Rozszerzono walidacje w `rank_service.py` z obsługą błędów i logowaniem
- Dodano walidację poprawności rang w bazie danych i automatyczną korekcję niepoprawnych wartości

### Naprawiono
- Naprawiono niezgodności walidacji między schematami a modelami
- Dodano walidację indeksów rang i obsługę błędów w funkcjach rang
- Poprawiono walidację accuracy w zakresie 0-100% w `count_passed_sessions`

## [0.6.5] – 2025-12-04
### Dodano
- System obsługi kursów walut z integracją API NBP (USD, EUR, GBP)
- Model `CurrencyRate` do przechowywania kursów walut
- Endpointy `/api/currency-rates/` do zarządzania kursami walut:
  - `GET /api/currency-rates/` - lista kursów walut
  - `GET /api/currency-rates/latest` - najnowsze kursy dla wszystkich walut
  - `GET /api/currency-rates/latest/{code}` - najnowszy kurs dla wybranej waluty
  - `POST /api/currency-rates/fetch` - pobranie aktualnych kursów z API NBP
  - `POST /api/currency-rates/convert` - konwersja kwoty między walutami
  - `GET /api/currency-rates/rate/{currency}` - aktualny kurs dla waluty
- Serwis `currency_service.py` z funkcjami konwersji walut
- Pole `currency` w modelu `UserSettings` do przechowywania preferowanej waluty użytkownika
- Pole `distance_unit` w modelu `UserSettings` do przechowywania preferowanej jednostki odległości (m/y)
- Automatyczne pobieranie kursów walut z API NBP przez HTTPS

### Zmieniono
- Rozszerzona lista czynności serwisowych w interfejsie użytkownika (25 pozycji zamiast 11)
- Ulepszona organizacja czynności serwisowych w sekcje tematyczne

## [0.6.0] – 2025-12-01
### Dodano
- Wsparcie dla wielojęzyczności w API (przygotowanie pod i18n)

## [0.5.5] – 2025-01-XX
### Dodano
- System rang użytkowników oparty na liczbie zaliczonych sesji strzeleckich
- Serwis `rank_service.py` z logiką obliczania rang na podstawie celności sesji
- Wymagania celności dla różnych poziomów doświadczenia:
  - Początkujący: ≥75%
  - Średniozaawansowany: ≥85%
  - Zaawansowany: ≥95%
- 20 poziomów rang od "Nowicjusz" (0-4 sesje) do "Legenda Toru" (200+ sesji)
- Automatyczna aktualizacja rangi po dodaniu, edycji lub usunięciu sesji strzeleckiej
- Endpoint `/api/account/rank` do pobierania informacji o randze użytkownika
- Pole `rank` w modelu `User` do przechowywania aktualnej rangi użytkownika
- Funkcja `ensure_user_exists` w `AccountService` do synchronizacji użytkowników z Supabase Auth

### Zmieniono
- Obliczanie celności (`accuracy_percent`) w sesjach strzeleckich - teraz zawsze obliczane jeśli dostępne są `hits` i `shots`, niezależnie od `distance_m`
- Ustawienia użytkownika (`UserSettings`) - dla zalogowanych użytkowników ustawienia są teraz permanentne (`expires_at = None`)

## [0.5.0] – 2025-01-XX
### Dodano
- Analiza zdjęć tarczy strzeleckiej przy użyciu AI (OpenAI Vision API)
- Endpoint do analizy zdjęć tarczy z automatycznym wykrywaniem trafień i obliczaniem celności
- Integracja z OpenAI Vision API do przetwarzania obrazów tarczy strzeleckiej

## [0.4.0] – 2025-01-XX
### Zmieniono
- Usunięto automatyczne zwracanie amunicji do magazynu przy usuwaniu sesji strzeleckiej
- Przy edycji sesji amunicja jest zwracana/odejmowana tylko w przypadku zmiany liczby strzałów (różnica)

## [0.3.8] – 2025-01-24
### Dodano
- Rozszerzone ustawienia użytkownika w modelu UserSettings:
  - `maintenance_rounds_limit` - limit strzałów do konserwacji (domyślnie 500)
  - `maintenance_days_limit` - limit czasu między konserwacjami w dniach (domyślnie 90)
  - `maintenance_notifications_enabled` - włącz/wyłącz powiadomienia o konserwacji (domyślnie true)
  - `low_ammo_notifications_enabled` - włącz/wyłącz powiadomienia o niskiej amunicji (domyślnie true)
  - `ai_analysis_intensity` - intensywność analizy AI (domyślnie "normalna")
  - `ai_auto_comments` - automatyczne komentarze AI (domyślnie false)

### Zmieniono
- Zaktualizowano schematy `UserSettingsRead` i `UserSettingsUpdate` o nowe pola
- Naprawiono funkcję `update_settings` w `UserSettingsService` - dodano obsługę wszystkich nowych pól
- Domyślne wartości ustawień są teraz ustawiane przy tworzeniu nowego rekordu ustawień

## [0.3.7.1] – 2025-01-XXd
### Naprawiono
- Naprawiono błąd `AttributeError: 'ShootingSessionRead' object has no attribute 'get'` przy usuwaniu sesji strzeleckich
- Naprawiono konflikt nazw funkcji `get_session` w routerze z funkcją `get_session` z `database.py`
- Ujednolicono nazwy parametrów z `db` na `session` w całym serwisie sesji strzeleckich
- Przywrócono funkcję `validate_ammo_gun_compatibility` która była zakomentowana
- Poprawiono obliczanie kosztu przy edycji sesji - zachowuje oryginalny koszt stały z pierwotnej sesji

### Zmieniono
- Refaktoryzacja sesji strzeleckich - usunięto stare pliki (`schemas/session.py`, `services/session_service.py`)
- Utworzono nowe pliki: `schemas/shooting_sessions.py`, `services/shooting_sessions_service.py`
- Ujednolicono architekturę - jeden model, jeden schema, jeden serwis, jeden router dla sesji strzeleckich
- Naprawiono endpointy PATCH i DELETE dla sesji strzeleckich
- Dodano `response_model=Dict[str, str]` dla DELETE endpoint aby uniknąć błędów serializacji
- Ujednolicono typ `distance_m` z `int` na `float` w modelu ShootingSession

### Dodano
- Nowe testy dla sesji strzeleckich w `tests/test_shooting_sessions.py`
- Walidacja uprawnień użytkownika w `delete_shooting_session`

## [0.3.5] – 2025-11-17
### Dodano
- Endpointy zarządzania kontem użytkownika (`/api/account`)
- Moduł konserwacji broni (`/api/maintenance`)
- Endpointy ustawień użytkownika (`/api/settings`)
- Zarządzanie wyposażeniem i akcesoriami (`/api/attachments`)
- Endpointy sesji strzeleckich (`/api/shooting-sessions`)
- Rozszerzone modele danych dla konserwacji i wyposażenia

### Zmieniono
- Rozszerzona funkcjonalność API o nowe moduły zarządzania sprzętem
- Ulepszona struktura endpointów dla lepszej organizacji funkcjonalności

## [0.3.1] – 2025-01-XX
### Dodano
- Pełny system autoryzacji użytkowników (rejestracja, logowanie, wylogowanie)
- Endpoint `/auth/me` do pobierania danych aktualnego użytkownika
- Walidacja duplikatów emaili przy rejestracji (status 409)

### Zmieniono
- Rejestracja zwraca tokeny, ale nie loguje automatycznie użytkownika

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



