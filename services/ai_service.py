from typing import Optional
from openai import OpenAI
from models import Gun
from settings import settings
from services.error_handler import ErrorHandler
import logging
import asyncio

logger = logging.getLogger(__name__)


class AIService:
    """
    Serwis generujący krótki komentarz AI na podstawie wyników strzeleckich.
    Uwzględnia poziom zaawansowania użytkownika (skill_level).
    """

    @staticmethod
    def _get_skill_level_tone(skill_level: str, accuracy: float) -> str:
        skill_level = (skill_level or "beginner").lower()
        is_good = accuracy >= 70
        is_poor = accuracy < 50

        
        if skill_level in ["beginner", "początkujący"]:
            return (
                "TON: bardzo łagodny, motywujący i wspierający. "
                "NIE używaj sarkazmu, NIE krytykuj ostro, "
                "NIE porównuj wyniku do żartu ani komedii. "
                "Podkreśl postęp i daj prostą, delikatną wskazówkę."
            )

        
        if skill_level in ["intermediate", "średniozaawansowany"]:
            if is_poor:
                return (
                    "TON: konstruktywny, rzeczowy. Wskaż najważniejszy błąd "
                    "i jedną praktyczną wskazówkę."
                )
            elif is_good:
                return (
                    "TON: profesjonalny i zbalansowany. Pochwal dobre elementy "
                    "i zaproponuj kierunek dalszego rozwoju."
                )
            else:
                return (
                    "TON: neutralny, zrównoważony – pochwała + jedna uwaga do poprawy."
                )

        
        if skill_level in ["advanced", "zaawansowany", "expert", "ekspert"]:
            if is_poor:
                return (
                    "TON: bardzo bezpośredni, sarkastyczny i twardy, ale konstruktywny. "
                    "Możesz wprost powiedzieć, że wynik jak na zawodowca wygląda słabo "
                    "lub wręcz komicznie. Nie bądź obraźliwy personalnie – krytykuj jedynie technikę."
                )
            elif is_good:
                return (
                    "TON: precyzyjny i ekspercki. Wskaż nawet drobne detale do korekty."
                )
            else:
                return (
                    "TON: bezpośredni, techniczny. Konkretnie nazwij błędy i podaj poprawki."
                )

        return "TON: profesjonalny i konstruktywny."

    @staticmethod
    async def generate_comment(
        gun: Gun,
        distance_m: float,
        hits: int,     
        shots: int,    
        accuracy: float,
        skill_level: str = "beginner",
        api_key: Optional[str] = None
    ) -> str:

        
        api_key = api_key or settings.openai_api_key
        if not api_key:
            return "Brak klucza API OpenAI."

        if len(api_key) < 10:
            return "Błąd: nieprawidłowy klucz API OpenAI."

        try:
            logger.info(f"Generowanie komentarza AI: {gun.name}, celność {accuracy}%")
            client = OpenAI(api_key=api_key)

           
            tone_instruction = AIService._get_skill_level_tone(skill_level, accuracy)

          
            gun_parts = [gun.name]
            if gun.type:
                gun_parts.append(f"typ: {gun.type}")
            if gun.caliber:
                gun_parts.append(f"kaliber: {gun.caliber}")

            gun_info = ", ".join(gun_parts)

    
            prompt = f"""
Oceń sesję strzelecką w maksymalnie 120 słowach (3–5 zdań).
Dane:
- Broń: {gun_info}
- Dystans: {distance_m} m
- Celność: {accuracy:.1f}%

{tone_instruction}

Uwzględnij charakterystykę broni (kaliber, zachowanie przy strzale, typ) oraz wpływ dystansu.
Podaj ocenę ogólną, jedną kluczową obserwację i jedną sugestię poprawy lub pochwałę.

JEŚLI zbliżasz się do limitu długości — zakończ pełnym zdaniem podsumowania.
Styl: techniczny, konkretny, po polsku.
"""

            logger.debug(f"Wywołanie OpenAI (gpt-4o-mini)")

            def _call_openai():
                return client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Jesteś instruktorem strzelectwa. ZAWSZE dostosowuj ton "
                                "do poziomu użytkownika zgodnie z instrukcją w wiadomości użytkownika. "
                                "Nigdy nie łam wymagań dotyczących tonu."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=350,   
                    temperature=0.5,
                    timeout=30.0
                )

            response = await asyncio.to_thread(_call_openai)

            
            if not response or not response.choices:
                return "Błąd AI: Pusta odpowiedź."

            msg = response.choices[0].message
            if not msg or not msg.content:
                return "Błąd AI: Brak treści w odpowiedzi."

            return msg.content.strip()

        except Exception as e:
            error_msg = ErrorHandler.handle_openai_error(e, "generowanie komentarza AI")
            logger.error(f"Błąd AI ({type(e).__name__}): {str(e)}", exc_info=True)
            return f"Błąd podczas generowania komentarza: {error_msg}"
