"""
Skrypt do aktualizacji user_id w bazie danych do aktualnego user_id z Supabase

Użycie:
1. Zaloguj się w aplikacji
2. Otwórz konsolę przeglądarki (F12) i wykonaj:
   localStorage.getItem('access_token')
3. Uruchom ten skrypt z tokenem jako argumentem:
   python3 update_user_id.py YOUR_SUPABASE_TOKEN
   
Lub podaj user_id bezpośrednio:
   python3 update_user_id.py --user-id YOUR_USER_ID
"""
import sys
import asyncio
from database import get_session
from models import Gun, Ammo, ShootingSession, Maintenance, Attachment
from sqlmodel import select
from settings import settings
from supabase import create_client

async def get_user_id_from_token(token: str):
    """Pobierz user_id z tokena Supabase"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        print("Błąd: Supabase nie jest skonfigurowane")
        return None
    
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        response = await asyncio.to_thread(supabase.auth.get_user, token)
        if response.user:
            return response.user.id
        return None
    except Exception as e:
        print(f"Błąd podczas pobierania user_id z tokena: {e}")
        return None

def update_user_id(new_user_id: str):
    """Zaktualizuj wszystkie rekordy do nowego user_id"""
    session = next(get_session())
    
    print(f"=== Aktualizacja user_id do: {new_user_id} ===\n")
    
    # Zaktualizuj broń
    guns = session.exec(select(Gun)).all()
    updated_guns = 0
    for gun in guns:
        if gun.user_id != new_user_id:
            gun.user_id = new_user_id
            session.add(gun)
            updated_guns += 1
    print(f"Zaktualizowano {updated_guns} rekordów broni")
    
    # Zaktualizuj amunicję
    ammo = session.exec(select(Ammo)).all()
    updated_ammo = 0
    for a in ammo:
        if a.user_id != new_user_id:
            a.user_id = new_user_id
            session.add(a)
            updated_ammo += 1
    print(f"Zaktualizowano {updated_ammo} rekordów amunicji")
    
    # Zaktualizuj sesje
    sessions = session.exec(select(ShootingSession)).all()
    updated_sessions = 0
    for s in sessions:
        if s.user_id != new_user_id:
            s.user_id = new_user_id
            session.add(s)
            updated_sessions += 1
    print(f"Zaktualizowano {updated_sessions} rekordów sesji strzeleckich")
    
    # Zaktualizuj konserwacje
    maintenance = session.exec(select(Maintenance)).all()
    updated_maintenance = 0
    for m in maintenance:
        if m.user_id != new_user_id:
            m.user_id = new_user_id
            session.add(m)
            updated_maintenance += 1
    print(f"Zaktualizowano {updated_maintenance} rekordów konserwacji")
    
    # Zaktualizuj wyposażenie
    attachments = session.exec(select(Attachment)).all()
    updated_attachments = 0
    for att in attachments:
        if att.user_id != new_user_id:
            att.user_id = new_user_id
            session.add(att)
            updated_attachments += 1
    print(f"Zaktualizowano {updated_attachments} rekordów wyposażenia")
    
    try:
        session.commit()
        print(f"\n✓ Sukces! Zaktualizowano wszystkie rekordy do user_id: {new_user_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"\n✗ Błąd podczas zapisywania: {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python3 update_user_id.py YOUR_SUPABASE_TOKEN")
        print("  python3 update_user_id.py --user-id YOUR_USER_ID")
        sys.exit(1)
    
    user_id = None
    
    if sys.argv[1] == "--user-id" and len(sys.argv) > 2:
        user_id = sys.argv[2]
    else:
        token = sys.argv[1]
        print(f"Pobieranie user_id z tokena Supabase...")
        user_id = await get_user_id_from_token(token)
    
    if not user_id:
        print("Nie udało się pobrać user_id. Sprawdź token lub podaj user_id bezpośrednio.")
        sys.exit(1)
    
    print(f"\nZnaleziono user_id: {user_id}\n")
    
    confirm = input("Czy na pewno chcesz zaktualizować wszystkie rekordy do tego user_id? (tak/nie): ")
    if confirm.lower() != 'tak':
        print("Anulowano.")
        sys.exit(0)
    
    update_user_id(user_id)

if __name__ == "__main__":
    asyncio.run(main())

