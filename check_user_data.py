"""
Skrypt do sprawdzenia i aktualizacji user_id w bazie danych
"""
from database import get_session
from models import Gun, Ammo, ShootingSession, Maintenance, Attachment
from sqlmodel import select

def check_and_update_user_data():
    session = next(get_session())
    
    print("=== Sprawdzanie danych w bazie ===\n")
    
    # Sprawdź broń
    guns = session.exec(select(Gun)).all()
    print(f"Broń w bazie ({len(guns)} rekordów):")
    user_ids = set()
    for g in guns:
        print(f"  - {g.name}: user_id = {g.user_id}")
        user_ids.add(g.user_id)
    
    # Sprawdź amunicję
    ammo = session.exec(select(Ammo)).all()
    print(f"\nAmunicja w bazie ({len(ammo)} rekordów):")
    for a in ammo:
        print(f"  - {a.name}: user_id = {a.user_id}")
        user_ids.add(a.user_id)
    
    # Sprawdź sesje
    sessions = session.exec(select(ShootingSession)).all()
    print(f"\nSesje strzeleckie w bazie ({len(sessions)} rekordów):")
    for s in sessions:
        print(f"  - Sesja {s.id[:8]}...: user_id = {s.user_id}")
        user_ids.add(s.user_id)
    
    # Sprawdź konserwacje
    maintenance = session.exec(select(Maintenance)).all()
    print(f"\nKonserwacje w bazie ({len(maintenance)} rekordów):")
    for m in maintenance:
        print(f"  - Konserwacja {m.id[:8]}...: user_id = {m.user_id}")
        user_ids.add(m.user_id)
    
    # Sprawdź wyposażenie
    attachments = session.exec(select(Attachment)).all()
    print(f"\nWyposażenie w bazie ({len(attachments)} rekordów):")
    for att in attachments:
        print(f"  - {att.name}: user_id = {att.user_id}")
        user_ids.add(att.user_id)
    
    print(f"\n=== Unikalne user_id w bazie: {len(user_ids)} ===")
    for uid in user_ids:
        print(f"  - {uid}")
    
    print("\n=== Instrukcje ===")
    print("Aby zaktualizować dane do Twojego user_id z Supabase:")
    print("1. Zaloguj się w aplikacji")
    print("2. Otwórz konsolę przeglądarki (F12)")
    print("3. Wykonaj: localStorage.getItem('access_token')")
    print("4. Użyj tego tokena do sprawdzenia user_id z Supabase")
    print("5. Lub zaktualizuj wszystkie rekordy do jednego z istniejących user_id")

if __name__ == "__main__":
    check_and_update_user_data()

