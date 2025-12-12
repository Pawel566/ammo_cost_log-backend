"""
Prosty skrypt do aktualizacji wszystkich rekordów do jednego user_id

Użycie:
python3 update_to_single_user.py [user_id]

Jeśli nie podasz user_id, użyje pierwszego znalezionego w bazie.
"""
import sys
from database import get_session
from models import Gun, Ammo, ShootingSession, Maintenance, Attachment
from sqlmodel import select

def update_all_to_user_id(target_user_id: str):
    session = next(get_session())
    
    print(f"=== Aktualizacja wszystkich rekordów do user_id: {target_user_id} ===\n")
    
    updated = {
        'guns': 0,
        'ammo': 0,
        'sessions': 0,
        'maintenance': 0,
        'attachments': 0
    }
    
    # Zaktualizuj broń
    guns = session.exec(select(Gun)).all()
    for gun in guns:
        if gun.user_id != target_user_id:
            gun.user_id = target_user_id
            session.add(gun)
            updated['guns'] += 1
    
    # Zaktualizuj amunicję
    ammo = session.exec(select(Ammo)).all()
    for a in ammo:
        if a.user_id != target_user_id:
            a.user_id = target_user_id
            session.add(a)
            updated['ammo'] += 1
    
    # Zaktualizuj sesje
    sessions = session.exec(select(ShootingSession)).all()
    for s in sessions:
        if s.user_id != target_user_id:
            s.user_id = target_user_id
            session.add(s)
            updated['sessions'] += 1
    
    # Zaktualizuj konserwacje
    maintenance = session.exec(select(Maintenance)).all()
    for m in maintenance:
        if m.user_id != target_user_id:
            m.user_id = target_user_id
            session.add(m)
            updated['maintenance'] += 1
    
    # Zaktualizuj wyposażenie
    attachments = session.exec(select(Attachment)).all()
    for att in attachments:
        if att.user_id != target_user_id:
            att.user_id = target_user_id
            session.add(att)
            updated['attachments'] += 1
    
    total = sum(updated.values())
    if total > 0:
        try:
            session.commit()
            print(f"✓ Zaktualizowano:")
            print(f"  - Broń: {updated['guns']}")
            print(f"  - Amunicja: {updated['ammo']}")
            print(f"  - Sesje: {updated['sessions']}")
            print(f"  - Konserwacje: {updated['maintenance']}")
            print(f"  - Wyposażenie: {updated['attachments']}")
            print(f"\n✓ Łącznie zaktualizowano {total} rekordów")
            return True
        except Exception as e:
            session.rollback()
            print(f"✗ Błąd: {e}")
            return False
    else:
        print("Wszystkie rekordy już mają poprawny user_id")
        return True

if __name__ == "__main__":
    session = next(get_session())
    
    if len(sys.argv) > 1:
        target_user_id = sys.argv[1]
    else:
        # Znajdź pierwszy user_id w bazie
        guns = session.exec(select(Gun)).limit(1).all()
        if guns:
            target_user_id = guns[0].user_id
            print(f"Używam pierwszego znalezionego user_id: {target_user_id}\n")
        else:
            print("Brak danych w bazie. Nie można zaktualizować.")
            sys.exit(1)
    
    update_all_to_user_id(target_user_id)

