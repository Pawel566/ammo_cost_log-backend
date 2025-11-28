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
        """
        Zwraca instrukcję dotyczącą tonu komentarza na podstawie poziomu zaawansowania i wyników.
        """
        skill_level = skill_level.lower() if skill_level else 'beginner'
        is_good = accuracy >= 70
        is_poor = accuracy < 50

        # Początkujący
        if skill_level in ['beginner', 'początkujący']:
            if is_poor:
                return (
                    "Ton bardzo łagodny, wspierający i motywujący. Podkreślaj postęp "
                    "i zachęcaj do dalszej praktyki."
                )
            elif is_good:
                return (
                    "Ton entuzjastyczny. Doceniaj postęp i zachęcaj do dalszego rozwoju."
                )
            else:
                return (
                    "Ton delikatnie konstruktywny. Chwal postęp, wskazując jedną rzecz do poprawy."
                )

        # Średniozaawansowani
        elif skill_level in ['intermediate', 'średniozaawansowany']:
            if is_poor:
                return (
                    "Ton konstruktywny, rzeczowy. Wskaż najważniejszy błąd oraz praktyczną wskazówkę."
                )
            elif is_good:
                return (
                    "Ton profesjonalny i zbalansowany. Doceniaj mocne strony i sugeruj kierunek rozwoju."
                )
            else:
                return (
                    "Ton zbalansowany – pochwała + konkretna uwaga do poprawy."
                )

        # Zaawansowani / Eksperci (można cisnąć)
        elif skill_level in ['advanced', 'zaawansowany', 'expert', 'ekspert']:
            if is_poor:
                return (
                    "Ton bardzo bezpośredni i sarkastyczny, ale konstruktywny. "
                    "Podkreśl, że wynik jak na zawodowca wygląda słabo – nawet komicznie. "
                    "Wskaż konkretne błędy techniczne w mocny sposób, bez owijania."
                )
            elif is_good:
                return (
                    "Ton precyzyjny i ekspertcki. Zwróć uwagę nawet na drobne detale do korekty."
                )
            else:
                return (
                    "Ton bezpośredni i techniczny. Wskaż najważniejsze błędy i konkretne poprawki."
                )

        # Fallback
        return "Ton profesjonalny i konstruktywny."

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

        if not api_key:
            api_key = settings.openai_api_key

        if not api_key:
            logger.error("Brak klucza API OpenAI w ustawieniach")
            return "Brak klucza API OpenAI. Skonfiguruj OPENAI_API_KEY."

        if len(api_key.strip()) < 10:
            logger.error("Klucz API OpenAI jest zbyt krótki")
            return "Błąd podczas generowania komentarza: Nieprawidłowy klucz API OpenAI"

        try:
            logger.info(f"Próba wygenerowania komentarza AI dla broni {gun.name}, celność: {accuracy:.1f}%")
            client = OpenAI(api_key=api_key)

            # Ustal ton wypowiedzi (skill_level + accuracy)
            tone_instruction = AIService._get_skill_level_tone(skill_level, accuracy)

            # Dane o broni - buduj szczegółowy opis
            gun_details = []
            gun_details.append(f"Nazwa: {gun.name}")
            if gun.type:
                gun_details.append(f"Typ: {gun.type}")
            if gun.caliber:
                gun_details.append(f"Kaliber: {gun.caliber}")
            
            gun_info = ", ".join(gun_details)

            # Finalny, zoptymalizowany prompt
            prompt = f"""
Oceń tę sesję strzelecką w maksymalnie 200 słowach.

Dane sesji:
- Broń: {gun_info}
- Dystans: {distance_m} m
- Trafienia: {hits}/{shots}
- Celność: {accuracy:.1f}%

{tone_instruction}

WAŻNE: W swoim komentarzu UWZGLĘDNIJ informacje o broni (typ, kaliber, charakterystyka). 
Oceń czy wynik jest odpowiedni dla tego typu broni i dystansu. 
Uwzględnij specyfikę broni w ocenie (np. pistolet vs karabinek, kaliber, typ).

Podaj krótką ocenę ogólną, najważniejszą obserwację związaną z bronią i wynikami, oraz jedną sugestię poprawy lub pochwałę.
Styl: rzeczowy, techniczny, w języku polskim.
"""

            logger.debug(f"Wysyłanie żądania do OpenAI z modelem gpt-4o-mini")
            
            # Wywołaj OpenAI w osobnym wątku, aby nie blokować event loop
            def _call_openai():
                return client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Jesteś instruktorem strzelectwa. Oceniasz wyniki krótko, "
                                "rzeczowo i profesjonalnie — ton dopasowany do poziomu użytkownika."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.5,
                    timeout=30.0
                )
            
            response = await asyncio.to_thread(_call_openai)
            logger.debug(f"Otrzymano odpowiedź z OpenAI: {response.choices[0].message.content[:50] if response.choices else 'brak'}")

            # Sprawdź czy odpowiedź jest poprawna
            if not response or not response.choices or len(response.choices) == 0:
                logger.error("OpenAI zwróciło pustą odpowiedź")
                return "Błąd podczas generowania komentarza: Pusta odpowiedź z OpenAI"
            
            message = response.choices[0].message
            if not message or not message.content:
                logger.error("OpenAI zwróciło odpowiedź bez treści")
                return "Błąd podczas generowania komentarza: Brak treści w odpowiedzi OpenAI"
            
            content = message.content.strip()
            if not content:
                logger.error("OpenAI zwróciło pustą treść")
                return "Błąd podczas generowania komentarza: Pusta treść w odpowiedzi OpenAI"
            
            return content

        except Exception as e:
            error_msg = ErrorHandler.handle_openai_error(e, "generowanie komentarza AI")
            logger.error(f"Błąd AI: {type(e).__name__}: {str(e)}", exc_info=True)
            return f"Błąd podczas generowania komentarza: {error_msg}"
