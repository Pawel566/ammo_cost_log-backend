from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlmodel import Session, select
from models import ShootingSession, User, Gun
from schemas.shooting_sessions import ShootingSessionRead, ShootingSessionCreate, ShootingSessionUpdate, MonthlySummary
from schemas.pagination import PaginatedResponse
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole
from services.shooting_sessions_service import ShootingSessionsService
from services.ai_service import AIService
from services.rank_service import update_user_rank
from services.account_service import AccountService
from services.user_settings_service import UserSettingsService
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import logging

try:
    from services.supabase_service import upload_target_image, get_signed_target_url, delete_target_image, get_target_image_base64
except ImportError:
    def upload_target_image(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")
    def get_signed_target_url(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")
    def delete_target_image(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")
    def get_target_image_base64(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shooting-sessions", tags=["Shooting Sessions"])


def convert_distance(distance_m: Optional[float], distance_unit: str) -> tuple[Optional[float], str]:
    """
    Konwertuje dystans z metrów na jednostki użytkownika.
    Zwraca (przeliczona_wartość, jednostka)
    """
    if distance_m is None:
        return None, distance_unit
    
    if distance_unit == "yd":
        # Konwersja metrów na jardy: 1 m = 1.09361 yd
        distance_yd = round(distance_m * 1.09361, 2)
        return distance_yd, "yd"
    else:
        # Domyślnie metry
        return round(distance_m, 2), "m"


async def create_session_read(session_obj: ShootingSession, db_session: Session, user: UserContext) -> ShootingSessionRead:
    """Tworzy ShootingSessionRead z konwersją jednostek dystansu"""
    # Pobierz ustawienia użytkownika
    user_settings = await UserSettingsService.get_settings(db_session, user)
    distance_unit = user_settings.distance_unit or "m"
    
    # Konwertuj dystans
    distance, unit = convert_distance(session_obj.distance_m, distance_unit)
    
    return ShootingSessionRead(
        id=session_obj.id,
        gun_id=session_obj.gun_id,
        ammo_id=session_obj.ammo_id,
        date=session_obj.date.isoformat() if hasattr(session_obj.date, 'isoformat') else str(session_obj.date),
        shots=session_obj.shots,
        cost=session_obj.cost,
        notes=session_obj.notes,
        distance_m=session_obj.distance_m,  # Oryginalna wartość w metrach
        distance=distance,  # Przeliczona wartość
        distance_unit=unit,  # Jednostka przeliczona
        hits=session_obj.hits,
        group_cm=session_obj.group_cm if hasattr(session_obj, 'group_cm') else None,
        accuracy_percent=session_obj.accuracy_percent,
        final_score=session_obj.final_score if hasattr(session_obj, 'final_score') else None,
        ai_comment=session_obj.ai_comment,
        session_type=session_obj.session_type if hasattr(session_obj, 'session_type') else 'standard',
        target_image_path=session_obj.target_image_path if hasattr(session_obj, 'target_image_path') else None,
        user_id=session_obj.user_id
    )


class MonthlySummaryResponse(PaginatedResponse[MonthlySummary]):
    pass

#
@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
async def create_shooting_session(
    session_data: ShootingSessionCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.create_shooting_session(session, user, session_data)
    
    # ⚡ Aktualizacja rangi - po commit sesji strzeleckiej
    try:
        def _ensure_user_and_update_rank(db_session: Session):
            db_user = AccountService.ensure_user_exists(db_session, user)
            return update_user_rank(db_user, db_session)
        
        logger.info(f"[RANK] Aktualizacja rangi dla użytkownika {user.user_id} po utworzeniu sesji. Sesja: shots={result['session'].shots}, hits={result['session'].hits}, accuracy={result['session'].accuracy_percent}")
        updated_rank = await asyncio.to_thread(lambda: _ensure_user_and_update_rank(session))
        logger.info(f"[RANK] Zaktualizowana ranga: {updated_rank}")
    except Exception as e:
        logger.error(f"[RANK] Błąd podczas aktualizacji rangi: {str(e)}", exc_info=True)
    
    # Konwertuj dystans do jednostek użytkownika
    user_settings = await UserSettingsService.get_settings(session, user)
    distance_unit = user_settings.distance_unit or "m"
    distance, unit = convert_distance(result["session"].distance_m, distance_unit)
    
    return {
        "id": result["session"].id,
        "gun_id": result["session"].gun_id,
        "ammo_id": result["session"].ammo_id,
        "date": result["session"].date.isoformat(),
        "shots": result["session"].shots,
        "cost": result["session"].cost,
        "notes": result["session"].notes,
        "distance_m": result["session"].distance_m,
        "distance": distance,
        "distance_unit": unit,
        "hits": result["session"].hits,
        "accuracy_percent": result["session"].accuracy_percent,
        "remaining_ammo": result["remaining_ammo"]
    }


@router.get("/", response_model=list[ShootingSessionRead])
@router.get("", response_model=list[ShootingSessionRead])
async def get_all_sessions(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1),
    gun_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None)
):
    try:
        result = await ShootingSessionsService.get_all_sessions(
            session, user, limit, offset, search, gun_id, date_from, date_to
        )
        sessions = result.get("items", [])
        return [
            await create_session_read(s, session, user)
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Błąd podczas pobierania sesji: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania sesji: {str(e)}")

@router.get("/summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(12, ge=1, le=120),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    try:
        result = await ShootingSessionsService.get_monthly_summary(session, user, limit, offset, search)
        return {
            "total": result.get("total", 0),
            "items": result.get("items", []),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Błąd podczas pobierania podsumowania: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania podsumowania: {str(e)}")


@router.post("/{session_id}/generate-ai-comment", response_model=Dict[str, Any])
async def generate_ai_comment(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.user, UserRole.admin]))
):
    """
    Generuje komentarz AI dla sesji strzeleckiej.
    Wymaga: dystans, liczba strzałów, oraz (opcjonalnie) zdjęcie tarczy lub liczba trafień.
    
    Przypadek A: brak trafień + zdjęcie -> Vision liczy trafienia i analizuje
    Przypadek B: trafienia + zdjęcie -> Vision tylko analizuje jakościowo
    Przypadek C: trafienia bez zdjęcia -> tylko tekstowa analiza
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Goście nie mogą generować komentarzy AI")
    
    # Pobierz sesję
    ss = ShootingSessionsService._get_session(session, session_id, user)
    if not ss:
        raise HTTPException(status_code=404, detail="Sesja nie została znaleziona")
    
    # Wymagane: dystans i liczba strzałów
    if not ss.distance_m or not ss.shots or ss.shots == 0:
        raise HTTPException(
            status_code=400, 
            detail="Sesja musi zawierać dystans i liczbę strzałów, aby wygenerować komentarz AI"
        )
    
    # Pobierz broń
    gun = session.get(Gun, ss.gun_id)
    if not gun:
        raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
    
    # Pobierz skill_level użytkownika
    def _get_skill_level(db_session: Session):
        query_user = select(User).where(User.user_id == user.user_id)
        user_record = db_session.exec(query_user).first()
        return user_record.skill_level if user_record else "beginner"
    
    skill_level = await asyncio.to_thread(_get_skill_level, session)
    
    # Pobierz język użytkownika
    user_settings = await UserSettingsService.get_settings(session, user)
    user_language = user_settings.language or "pl"
    
    # Sprawdź czy jest zdjęcie tarczy
    target_image_base64 = None
    if ss.target_image_path:
        try:
            logger.info(f"Pobieranie zdjęcia tarczy: {ss.target_image_path}")
            target_image_base64 = await asyncio.to_thread(get_target_image_base64, ss.target_image_path)
            logger.info(f"Zdjęcie tarczy pobrane pomyślnie, rozmiar base64: {len(target_image_base64) if target_image_base64 else 0}")
        except Exception as e:
            logger.warning(f"Nie udało się pobrać zdjęcia tarczy: {str(e)}", exc_info=True)
            target_image_base64 = None
    
    # Określ przypadek
    has_hits = ss.hits is not None
    has_image = target_image_base64 is not None
    
    logger.info(f"Analiza AI - has_hits: {has_hits}, has_image: {has_image}, distance_m: {ss.distance_m}, shots: {ss.shots}")
    
    try:
        if has_image:
            # Przypadek A lub B: użyj Vision
            logger.info(f"Wywołanie Vision API dla sesji {session_id}")
            vision_result = await AIService.analyze_target_with_vision(
                gun=gun,
                distance_m=ss.distance_m,
                shots=ss.shots,
                hits=ss.hits if has_hits else None,
                target_image_base64=target_image_base64,
                skill_level=skill_level,
                language=user_language
            )
            
            if vision_result:
                logger.info(f"Vision API zwróciło wynik: hits={vision_result.get('hits')}, accuracy={vision_result.get('accuracy')}")
                # Przypadek A: Vision policzyło trafienia
                if not has_hits:
                    ss.hits = vision_result["hits"]
                    ss.accuracy_percent = vision_result["accuracy"]
                
                ss.ai_comment = vision_result["comment"]
                session.add(ss)
                await asyncio.to_thread(session.commit)
                await asyncio.to_thread(session.refresh, ss)
                
                return {
                    "ai_comment": vision_result["comment"],
                    "hits": vision_result.get("hits"),
                    "accuracy": vision_result.get("accuracy")
                }
            else:
                logger.warning(f"Vision API zwróciło None dla sesji {session_id}")
                # Vision nie zadziałało - sprawdź przyczynę
                if not has_hits:
                    # Sprawdź czy problem jest z kluczem API
                    if not settings.openai_api_key:
                        raise HTTPException(
                            status_code=400,
                            detail="Brak klucza OpenAI API. Skonfiguruj OPENAI_API_KEY w zmiennych środowiskowych."
                        )
                    raise HTTPException(
                        status_code=400,
                        detail="Nie udało się policzyć trafień ze zdjęcia. Sprawdź czy zdjęcie jest poprawne lub podaj liczbę trafień ręcznie."
                    )
        
        # Przypadek C lub fallback: zwykła analiza tekstowa
        if not has_hits:
            raise HTTPException(
                status_code=400,
                detail="Podaj liczbę trafień lub dodaj zdjęcie tarczy, aby wygenerować komentarz AI"
            )
        
        if not ss.accuracy_percent:
            ss.accuracy_percent = (ss.hits / ss.shots * 100) if ss.shots > 0 else 0
        
        ai_comment = await AIService.generate_comment(
            gun=gun,
            distance_m=ss.distance_m,
            hits=ss.hits,
            shots=ss.shots,
            accuracy=ss.accuracy_percent,
            skill_level=skill_level,
            language=user_language
        )
        
        # Sprawdź czy komentarz zawiera błąd
        if ai_comment.startswith("Błąd podczas generowania komentarza") or ai_comment.startswith("Brak klucza API"):
            raise HTTPException(status_code=500, detail=ai_comment)
        
        # Zapisz komentarz w sesji
        ss.ai_comment = ai_comment
        session.add(ss)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ss)
        
        return {"ai_comment": ai_comment}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas generowania komentarza AI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania komentarza AI: {str(e)}")


@router.get("/{session_id}", response_model=ShootingSessionRead)
async def get_shooting_session(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = ShootingSessionsService._get_session(session, session_id, user)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return await create_session_read(ss, session, user)


@router.patch("/{session_id}", response_model=Dict[str, Any])
async def update_session(
    session_id: str,
    session_data: ShootingSessionUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.update_shooting_session(session, session_id, user, session_data)
    ss = result["session"]
    
    # ⚡ Aktualizacja rangi - po aktualizacji sesji
    try:
        def _ensure_user_and_update_rank(db_session: Session):
            db_user = AccountService.ensure_user_exists(db_session, user)
            return update_user_rank(db_user, db_session)
        
        logger.info(f"[RANK] Aktualizacja rangi dla użytkownika {user.user_id} po aktualizacji sesji")
        updated_rank = await asyncio.to_thread(lambda: _ensure_user_and_update_rank(session))
        logger.info(f"[RANK] Zaktualizowana ranga: {updated_rank}")
    except Exception as e:
        logger.error(f"[RANK] Błąd podczas aktualizacji rangi: {str(e)}", exc_info=True)
    
    # Konwertuj dystans do jednostek użytkownika
    user_settings = await UserSettingsService.get_settings(session, user)
    distance_unit = user_settings.distance_unit or "m"
    distance, unit = convert_distance(ss.distance_m, distance_unit)
    
    return {
        "id": ss.id,
        "gun_id": ss.gun_id,
        "ammo_id": ss.ammo_id,
        "date": ss.date.isoformat() if hasattr(ss.date, 'isoformat') else str(ss.date),
        "shots": ss.shots,
        "cost": ss.cost,
        "notes": ss.notes,
        "distance_m": ss.distance_m,
        "distance": distance,
        "distance_unit": unit,
        "hits": ss.hits,
        "accuracy_percent": ss.accuracy_percent,
        "remaining_ammo": result.get("remaining_ammo")
    }


@router.delete("/{session_id}", response_model=Dict[str, str])
async def delete_session(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.delete_shooting_session(session, session_id, user)
    
    # ⚡ Aktualizacja rangi - po usunięciu sesji
    try:
        def _ensure_user_and_update_rank(db_session: Session):
            db_user = AccountService.ensure_user_exists(db_session, user)
            return update_user_rank(db_user, db_session)
        
        logger.info(f"[RANK] Aktualizacja rangi dla użytkownika {user.user_id} po usunięciu sesji")
        updated_rank = await asyncio.to_thread(lambda: _ensure_user_and_update_rank(session))
        logger.info(f"[RANK] Zaktualizowana ranga: {updated_rank}")
    except Exception as e:
        logger.error(f"[RANK] Błąd podczas aktualizacji rangi: {str(e)}", exc_info=True)
    
    return result


@router.post("/{session_id}/target-image")
async def upload_target_image_endpoint(
    session_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.user, UserRole.admin]))
):
    """
    Upload target image to Supabase Storage.
    Only authenticated users (not guests) can upload images.
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Goście nie mogą dodawać zdjęć")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Plik musi być obrazem")
    
    ss = ShootingSessionsService._get_session(session, session_id, user)
    if not ss:
        raise HTTPException(status_code=404, detail="Sesja nie została znaleziona")
    
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Plik jest zbyt duży (max 10MB)")
    
    filename = file.filename or f"target_{session_id}.jpg"
    
    try:
        image_path = await asyncio.to_thread(
            upload_target_image,
            user.user_id,
            session_id,
            filename,
            file_bytes
        )
        
        if ss.target_image_path:
            try:
                await asyncio.to_thread(delete_target_image, ss.target_image_path)
            except Exception:
                pass
        
        ss.target_image_path = image_path
        session.add(ss)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ss)
        
        return {"image_path": image_path}
    except ValueError as e:
        raise HTTPException(status_code=503, detail="Usługa przechowywania zdjęć nie jest dostępna. Skonfiguruj Supabase Storage.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas przesyłania zdjęcia: {str(e)}")


@router.get("/{session_id}/target-image")
async def get_target_image(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    """
    Get signed URL for target image.
    Returns null if no image is uploaded or if Supabase is not configured.
    Only the owner of the session can see the image.
    """
    try:
        ss = ShootingSessionsService._get_session(session, session_id, user)
        if not ss:
            return {"url": None}
        
        if not ss.target_image_path:
            return {"url": None}
        
        try:
            signed_url = await asyncio.to_thread(get_signed_target_url, ss.target_image_path)
            return {"url": signed_url}
        except (ValueError, Exception) as e:
            print(f"Warning: Could not generate signed URL: {e}")
            return {"url": None}
    except Exception as e:
        print(f"Warning: Could not get target image: {e}")
        return {"url": None}


@router.delete("/{session_id}/target-image")
async def delete_target_image_endpoint(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.user, UserRole.admin]))
):
    """
    Delete target image from session.
    Only authenticated users (not guests) can delete images.
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Goście nie mogą usuwać zdjęć")
    
    ss = ShootingSessionsService._get_session(session, session_id, user)
    if not ss:
        raise HTTPException(status_code=404, detail="Sesja nie została znaleziona")
    
    if not ss.target_image_path:
        raise HTTPException(status_code=404, detail="Sesja nie ma zdjęcia tarczy")
    
    try:
        await asyncio.to_thread(delete_target_image, ss.target_image_path)
        ss.target_image_path = None
        session.add(ss)
        await asyncio.to_thread(session.commit)
        return {"message": "Zdjęcie tarczy zostało usunięte"}
    except ValueError as e:
        raise HTTPException(status_code=503, detail="Usługa przechowywania zdjęć nie jest dostępna.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas usuwania zdjęcia: {str(e)}")