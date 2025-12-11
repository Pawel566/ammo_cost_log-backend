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
    if not user or not user.user_id:
        logger.error("[RANK] Brak użytkownika lub user_id")
        return 0
    
    required_accuracy = _get_required_accuracy(user.skill_level)
    logger.info(f"[RANK] Liczenie zaliczonych sesji dla użytkownika {user.user_id}, skill_level={user.skill_level}, wymagana celność={required_accuracy}%")

    stmt = (
        select(ShootingSession)
        .where(ShootingSession.user_id == user.user_id)
    )
    sessions = db.exec(stmt).all()
    logger.info(f"[RANK] Znaleziono {len(sessions)} sesji dla użytkownika {user.user_id}")

    passed_count = 0

    for s in sessions:
        accuracy = s.accuracy_percent

        # Legacy / bezpieczeństwo: jeśli accuracy brak, a są hits + shots → policz
        if accuracy is None:
            if s.hits is not None and s.shots is not None and s.shots > 0:
                accuracy = SessionCalculationService.calculate_accuracy(s.hits, s.shots)
                logger.debug(f"[RANK] Sesja {s.id}: obliczono accuracy={accuracy}% z hits={s.hits}, shots={s.shots}")

        if accuracy is not None:
            # Walidacja: accuracy powinno być między 0 a 100
            if accuracy < 0 or accuracy > 100:
                logger.warning(f"[RANK] Sesja {s.id}: nieprawidłowa wartość accuracy={accuracy}%, pomijana")
                continue
            
            logger.debug(f"[RANK] Sesja {s.id}: accuracy={accuracy}%, wymagana={required_accuracy}%, zaliczona={accuracy >= required_accuracy}")
            if accuracy >= required_accuracy:
                passed_count += 1
        else:
            logger.debug(f"[RANK] Sesja {s.id}: brak accuracy (hits={s.hits}, shots={s.shots}), pomijana")

    # Upewnij się, że wynik nie jest ujemny
    passed_count = max(0, passed_count)
    logger.info(f"[RANK] Użytkownik {user.user_id}: {passed_count} zaliczonych sesji z {len(sessions)} wszystkich")
    return passed_count


def get_rank_name(passed_sessions: int) -> str:
    """
    Zwraca nazwę rangi dla danej liczby zaliczonych sesji.
    """
    if passed_sessions < 0:
        logger.warning(f"[RANK] Ujemna liczba sesji: {passed_sessions}, zwracam 'Nowicjusz'")
        return "Nowicjusz"
    
    for min_s, max_s, name in RANKS:
        if min_s <= passed_sessions <= max_s:
            return name
    # Bezpieczny fallback
    logger.warning(f"[RANK] Nie znaleziono rangi dla {passed_sessions} sesji, zwracam 'Nowicjusz'")
    return "Nowicjusz"


def _find_rank_index_by_name(rank_name: str) -> int:
    """
    Znajduje indeks rangi po nazwie. Zwraca 0 (Nowicjusz) jeśli nie znajdzie.
    """
    if not rank_name:
        logger.warning(f"[RANK] Pusta nazwa rangi, zwracam indeks 0 (Nowicjusz)")
        return 0
    
    for i, (_, _, name) in enumerate(RANKS):
        if name == rank_name:
            return i
    
    logger.warning(f"[RANK] Nie znaleziono rangi '{rank_name}', zwracam indeks 0 (Nowicjusz)")
    return 0


def is_valid_rank_name(rank_name: str) -> bool:
    """
    Sprawdza czy nazwa rangi jest poprawna (istnieje w liście RANKS).
    """
    if not rank_name:
        return False
    return _find_rank_index_by_name(rank_name) >= 0


def update_user_rank(user: User, db: Session) -> str:
    """
    Przelicza liczbę zaliczonych sesji, wyznacza rangę i zapisuje ją w user.rank,
    jeśli się zmieniła. Zwraca aktualną nazwę rangi.
    """
    if not user:
        logger.error("[RANK] Brak użytkownika w update_user_rank")
        return "Nowicjusz"
    
    passed = count_passed_sessions(user, db)
    new_rank = get_rank_name(passed)

    # Walidacja: sprawdź czy nowa ranga jest poprawna
    rank_index = _find_rank_index_by_name(new_rank)
    if rank_index < 0 or rank_index >= len(RANKS):
        logger.error(f"[RANK] Nieprawidłowa ranga '{new_rank}', ustawiam 'Nowicjusz'")
        new_rank = "Nowicjusz"

    # Sprawdź czy ranga w bazie jest poprawna (może być niepoprawna z powodu błędów w danych)
    current_rank_index = _find_rank_index_by_name(user.rank or "Nowicjusz")
    if current_rank_index < 0 or current_rank_index >= len(RANKS):
        logger.warning(f"[RANK] Użytkownik {user.user_id}: niepoprawna ranga w bazie '{user.rank}', koryguję na '{new_rank}'")
        user.rank = new_rank
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.rank != new_rank:
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
    if not user:
        logger.error("[RANK] Brak użytkownika w get_rank_info")
        return {
            "rank": "Nowicjusz",
            "passed_sessions": 0,
            "current_rank_min": 0,
            "current_rank_max": 4,
            "next_rank": "Adepciak",
            "next_rank_min": 5,
            "progress_percent": 0.0,
            "sessions_to_next_rank": 5,
            "is_max_rank": False,
        }
    
    passed = count_passed_sessions(user, db)
    current_rank_name = get_rank_name(passed)
    current_index = _find_rank_index_by_name(current_rank_name)

    # Walidacja indeksu
    if current_index < 0 or current_index >= len(RANKS):
        logger.error(f"[RANK] Nieprawidłowy indeks rangi: {current_index}, ustawiam na 0")
        current_index = 0
        current_rank_name = "Nowicjusz"

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
