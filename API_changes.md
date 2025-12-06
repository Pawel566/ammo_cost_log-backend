# Zmiany w API

## Podsumowanie

Refaktoryzacja backendu nie zmienia logiki biznesowej ani endpointów API. Wszystkie endpointy działają tak samo jak wcześniej, ale wewnętrzna implementacja została uproszczona i ulepszona.

## Zmiany w odpowiedziach API

### Usunięte pola z odpowiedzi

Następujące pola zostały usunięte z odpowiedzi API (nie były używane przez frontend):

#### GET /api/guns/
- ❌ Usunięto: `expires_at` z każdego obiektu broni

#### GET /api/ammo/
- ❌ Usunięto: `expires_at` z każdego obiektu amunicji

#### GET /api/maintenance/
- ❌ Usunięto: `expires_at` z każdego obiektu konserwacji

#### GET /api/attachments/
- ❌ Usunięto: `expires_at` z każdego obiektu załącznika

#### GET /api/shooting-sessions/
- ❌ Usunięto: `expires_at` z każdego obiektu sesji strzeleckiej

### Zachowane pola

Wszystkie inne pola pozostają bez zmian:
- ✅ Wszystkie pola identyfikacyjne (id, user_id, etc.)
- ✅ Wszystkie pola danych (name, caliber, shots, cost, etc.)
- ✅ Wszystkie pola relacji (gun_id, ammo_id, etc.)
- ✅ `expires_at` w odpowiedziach dotyczących użytkowników (jeśli dotyczy)

## Kompatybilność z frontendem

✅ **Pełna kompatybilność wsteczna**

Frontend (wersja 0.6.5-units) nie używa pól `expires_at` w odpowiedziach API dla broni, amunicji, konserwacji, załączników i sesji strzeleckich. Te pola były używane tylko wewnętrznie przez backend do zarządzania sesjami gości.

## Endpointy - bez zmian

Wszystkie endpointy działają identycznie:

- ✅ `GET /api/guns/` - bez zmian
- ✅ `POST /api/guns/` - bez zmian
- ✅ `PUT /api/guns/{id}` - bez zmian
- ✅ `DELETE /api/guns/{id}` - bez zmian
- ✅ `GET /api/ammo/` - bez zmian
- ✅ `POST /api/ammo/` - bez zmian
- ✅ `PUT /api/ammo/{id}` - bez zmian
- ✅ `DELETE /api/ammo/{id}` - bez zmian
- ✅ `GET /api/maintenance/` - bez zmian
- ✅ `POST /api/maintenance/` - bez zmian
- ✅ `GET /api/attachments/` - bez zmian
- ✅ `POST /api/attachments/` - bez zmian
- ✅ `GET /api/shooting-sessions/` - bez zmian
- ✅ `POST /api/shooting-sessions/` - bez zmian
- ✅ Wszystkie inne endpointy - bez zmian

## Obsługa błędów

Odpowiedzi błędów są teraz bardziej spójne:

- `404 Not Found` - używany przez `NotFoundError`
- `403 Forbidden` - używany przez `ForbiddenError`
- `400 Bad Request` - używany przez `BadRequestError`

Komunikaty błędów pozostają takie same, tylko źródło jest ujednolicone.

## Wydajność

- ✅ Usunięto niepotrzebne operacje `asyncio.to_thread` dla operacji DB
- ✅ Uproszczone zapytania SQL (usunięto filtrowanie po `expires_at`)
- ✅ Szybsze operacje CRUD dzięki bezpośrednim wywołaniom SQLModel

## Sesje gości

Sesje gości nadal działają poprawnie:
- ✅ Goście mogą tworzyć dane (bronie, amunicję, sesje, etc.)
- ✅ Dane gości są izolowane per sesja
- ✅ Sesje gości wygasają po 24 godzinach (lub zgodnie z konfiguracją)
- ✅ `expires_at` jest zarządzany tylko na poziomie użytkownika (User/UserSettings)

## Testowanie

Aby przetestować zmiany:

1. Uruchom backend: `python3 -m uvicorn main:app --reload`
2. Sprawdź endpointy używane przez frontend
3. Zweryfikuj, że wszystkie operacje działają poprawnie
4. Sprawdź logi - nie powinno być błędów związanych z `expires_at`


