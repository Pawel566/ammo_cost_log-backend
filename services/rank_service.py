from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sqlmodel import Session, select

from models import User, ShootingSession
from services.shooting_sessions_service import SessionCalculationService

logger = logging.getLogger(__name__)


# Minimalne wymagania celności dla zaliczenia sesji
ACCURACY_REQUIREMENTS: Dict[str, int] = {
    "beginner": 75,
    "intermediate": 85,
    "advanced": 95,
}


# Przedziały rang: (min_passed_sessions, max_passed_sessions, nazwa)
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
    (200, 999_999_999, "Legenda Toru"),
]


def _get_required_accuracy(skill_level: str) -> int:
    """
    Zwraca wymagany próg celności dla danego poziomu zaawansowania.
    Domyślnie 75%, jeśli skill_level jest nieznany.
    """
    return ACCURACY_REQUIREMENTS.get(skill_level or "beginner", 75)


def count_passed_sessions(user: User, db: Session) -> int:
    """
    Liczy ile sesji użytkownika spełnia wymagania rangi.

    Zasady:
    - bierze wszystkie sesje danego usera (standard + advanced),
    - jeśli accuracy_percent jest ustawione → używa go,
    - jeśli brak accuracy_percent, ale są hits + shots → liczy accuracy,
    - sesja liczy się, jeśli accuracy >= wymagany próg dla skill_level.
    """
    required_accuracy = _get_required_accuracy(user.skill_level)

    stmt = (
        select(ShootingSession)
        .where(ShootingSession.user_id == user.user_id)
    )
    sessions = db.exec(stmt).all()

    passed_count = 0

    for s in sessions:
        accuracy = s.accuracy_percent

        # Legacy / bezpieczeństwo: jeśli accuracy brak, a są hits + shots → policz
        if accuracy is None:
            if s.hits is not None and s.shots is not None and s.shots > 0:
                accuracy = SessionCalculationService.calculate_accuracy(s.hits, s.shots)

        if accuracy is not None and accuracy >= required_accuracy:
            passed_count += 1

    return passed_count


def get_rank_name(passed_sessions: int) -> str:
    """
    Zwraca nazwę rangi dla danej liczby zaliczonych sesji.
    """
    for min_s, max_s, name in RANKS:
        if min_s <= passed_sessions <= max_s:
            return name
    # Bezpieczny fallback
    return "Nowicjusz"


def _find_rank_index_by_name(rank_name: str) -> int:
    for i, (_, _, name) in enumerate(RANKS):
        if name == rank_name:
            return i
    return 0


def update_user_rank(user: User, db: Session) -> str:
    """
    Przelicza liczbę zaliczonych sesji, wyznacza rangę i zapisuje ją w user.rank,
    jeśli się zmieniła. Zwraca aktualną nazwę rangi.
    """
    passed = count_passed_sessions(user, db)
    new_rank = get_rank_name(passed)

    if user.rank != new_rank:
        logger.info(
            f"[RANK] Użytkownik {user.user_id}: zmiana rangi "
            f"z '{user.rank}' na '{new_rank}' (zaliczone sesje: {passed})"
        )
        user.rank = new_rank
        db.add(user)
        db.commit()
        db.refresh(user)

    return user.rank


def get_rank_info(user: User, db: Session) -> Dict[str, Any]:
    """
    Zwraca pełne info o randze użytkownika, w tym:
    - rank: aktualna nazwa rangi
    - passed_sessions: liczba zaliczonych sesji
    - current_rank_min / current_rank_max: przedział dla aktualnej rangi
    - next_rank: nazwa kolejnej rangi (lub None, jeśli max)
    - next_rank_min: minimalna liczba sesji dla kolejnej rangi (lub None)
    - progress_percent: progres w % w obrębie aktualnej rangi
    - sessions_to_next_rank: ile sesji brakuje do kolejnej rangi
    - is_max_rank: czy osiągnięto najwyższą rangę
    """
    passed = count_passed_sessions(user, db)
    current_rank_name = get_rank_name(passed)
    current_index = _find_rank_index_by_name(current_rank_name)

    current_min, current_max, _ = RANKS[current_index]

    # Domyślnie załóż, że nie jesteśmy na max rangi
    is_max_rank = current_index == len(RANKS) - 1
    next_rank_name: Optional[str] = None
    next_rank_min: Optional[int] = None

    if not is_max_rank:
        next_min, next_max, next_name = RANKS[current_index + 1]
        next_rank_name = next_name
        next_rank_min = next_min

    # Progres w obrębie aktualnej rangi
    if is_max_rank or next_rank_min is None:
        progress_percent = 100.0
        sessions_to_next = 0
    else:
        span = max(1, next_rank_min - current_min)
        progress_in_span = max(0, passed - current_min)
        progress_percent = (progress_in_span / span) * 100.0
        progress_percent = max(0.0, min(100.0, progress_percent))

        # Ile sesji brakuje do kolejnej rangi
        sessions_to_next = max(0, next_rank_min - passed)

    return {
        "rank": current_rank_name,
        "passed_sessions": passed,
        "current_rank_min": current_min,
        "current_rank_max": current_max,
        "next_rank": next_rank_name,
        "next_rank_min": next_rank_min,
        "progress_percent": progress_percent,
        "sessions_to_next_rank": sessions_to_next,
        "is_max_rank": is_max_rank,
    }


def get_rank_info_by_user_id(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Wygodny helper: pobiera usera po user_id i zwraca get_rank_info.
    Możesz tego używać np. w endpointzie /me/rank.
    """
    user = db.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    return get_rank_info(user, db)
