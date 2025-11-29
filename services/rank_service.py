from sqlmodel import Session, select

from models.user import User
from models.shooting_session import ShootingSession

ACCURACY_REQUIREMENTS = {
    "beginner": 75,
    "intermediate": 85,
    "advanced": 95,
}

RANKS = [
    (0, 4, "Nowicjusz"),
    (5, 9, "Adepciak"),
    (10, 14, "Stabilny Strzelec"),
    (15, 19, "Celny Strzelec"),
    (20, 29, "Precyzyjny Strzelec"),
    (30, 39, "Zaawansowany Strzelec"),
    (40, 49, "Szybki Operator"),
    (50, 59, "Pewna Ręka"),
    (60, 69, "Taktyk"),
    (70, 79, "Specjalista Celności"),
    (80, 89, "Ekspert Celności"),
    (90, 99, "Strzelec Polowy"),
    (100, 109, "Analizator"),
    (110, 119, "Strzelec Taktyczny"),
    (120, 129, "Weteran Toru"),
    (130, 139, "Mistrz Kontroli"),
    (140, 149, "Elita Precyzji"),
    (150, 169, "Dominator Tarczy"),
    (170, 199, "Mistrz Linii Ognia"),
    (200, 999999999, "Legenda Toru"),
]


def count_passed_sessions(user: User, db: Session) -> int:
    required_accuracy = ACCURACY_REQUIREMENTS.get(user.skill_level, 75)
    statement = (
        select(ShootingSession)
        .where(
            ShootingSession.user_id == user.user_id,
            ShootingSession.accuracy_percent >= required_accuracy
        )
    )
    sessions = db.exec(statement).all()
    return len(sessions)


def get_rank_name(passed_sessions: int) -> str:
    for min_s, max_s, name in RANKS:
        if min_s <= passed_sessions <= max_s:
            return name
    return "Nowicjusz"


def update_user_rank(user: User, db: Session) -> str:
    passed = count_passed_sessions(user, db)
    new_rank = get_rank_name(passed)
    if user.rank != new_rank:
        user.rank = new_rank
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.rank


def get_rank_info(user: User, db: Session) -> dict:
    passed = count_passed_sessions(user, db)
    current_rank = get_rank_name(passed)
    
    current_rank_index = None
    for i, (min_s, max_s, name) in enumerate(RANKS):
        if name == current_rank:
            current_rank_index = i
            break
    
    if current_rank_index is None:
        current_rank_index = 0
        current_rank = "Nowicjusz"
    
    next_rank = None
    next_rank_min = None
    is_max_rank = False
    if current_rank_index < len(RANKS) - 1:
        next_rank_min, next_rank_max, next_rank = RANKS[current_rank_index + 1]
    else:
        is_max_rank = True
    
    current_rank_min, current_rank_max, _ = RANKS[current_rank_index]
    
    progress_percent = 0
    if next_rank_min is not None:
        progress_percent = ((passed - current_rank_min) / (next_rank_min - current_rank_min)) * 100
        progress_percent = max(0, min(100, progress_percent))
    else:
        progress_percent = 100
    
    return {
        "rank": current_rank,
        "passed_sessions": passed,
        "current_rank_min": current_rank_min,
        "current_rank_max": current_rank_max,
        "next_rank": next_rank,
        "next_rank_min": next_rank_min,
        "progress_percent": progress_percent,
        "is_max_rank": is_max_rank
    }

