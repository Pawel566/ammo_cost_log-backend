from typing import Optional, Dict, Tuple
from openai import OpenAI
from models import Gun
from settings import settings
from services.error_handler import ErrorHandler
import logging
import asyncio
import base64

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

    @staticmethod
    async def analyze_target_with_vision(
        gun: Gun,
        distance_m: float,
        shots: int,
        hits: Optional[int] = None,
        target_image_base64: Optional[str] = None,
        skill_level: str = "beginner",
        api_key: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analizuje zdjęcie tarczy za pomocą OpenAI Vision API.
        
        Przypadek A: hits=None, target_image_base64 podane -> AI liczy trafienia i analizuje
        Przypadek B: hits podane, target_image_base64 podane -> AI tylko analizuje jakościowo
        Przypadek C: hits podane, target_image_base64=None -> zwraca None (użyj generate_comment)
        
        Returns:
            Dict z kluczami: hits (int, tylko przypadek A), comment (str), accuracy (float)
            Lub None jeśli Vision nie powinno być używane
        """
        api_key = api_key or settings.openai_api_key
        if not api_key:
            return None
        
        if len(api_key) < 10:
            return None
        
        # Wymagania dla Vision: dystans, liczba strzałów, zdjęcie
        if not distance_m or not shots or not target_image_base64:
            return None
        
        try:
            logger.info(f"Analiza Vision: {gun.name}, dystans {distance_m}m, {shots} strzałów, hits={'auto' if hits is None else hits}")
            client = OpenAI(api_key=api_key)
            
            gun_parts = [gun.name]
            if gun.type:
                gun_parts.append(f"typ: {gun.type}")
            if gun.caliber:
                gun_parts.append(f"kaliber: {gun.caliber}")
            gun_info = ", ".join(gun_parts)
            
            tone_instruction = AIService._get_skill_level_tone(skill_level, 0)  # Tymczasowo 0, będzie obliczone
            
            if hits is None:
                # Przypadek A: AI liczy trafienia
                prompt = f"""
Przeanalizuj zdjęcie tarczy strzeleckiej i wykonaj następujące zadania:

1. POLICZ DOKŁADNIE liczbę trafień (otworów po kulach) na tarczy
2. Oceń skupienie strzałów (czy są skupione w jednym miejscu, czy rozproszone)
3. Zidentyfikuj błędy techniczne:
   - ściąganie spustu (strzały w dół/lewo/dół-lewo)
   - dry-fire błędy (brak kontroli oddechu)
   - ucieczka broni (strzały w górę/prawo)
   - kontrola oddechu
   - inne zauważalne problemy

Dane kontekstowe:
- Broń: {gun_info}
- Dystans: {distance_m} m
- Liczba strzałów: {shots}

{tone_instruction}

Odpowiedz w formacie JSON:
{{
  "hits": <liczba trafień jako liczba>,
  "analysis": "<analiza skupienia i błędów w maksymalnie 120 słowach, po polsku>"
}}
"""
            else:
                # Przypadek B: AI tylko analizuje jakościowo
                accuracy = (hits / shots * 100) if shots > 0 else 0
                tone_instruction = AIService._get_skill_level_tone(skill_level, accuracy)
                
                prompt = f"""
Przeanalizuj zdjęcie tarczy strzeleckiej i wykonaj analizę jakościową.

UŻYWAMY WPISANYCH DANYCH: {hits} trafień z {shots} strzałów (celność {accuracy:.1f}%)

NIE licz trafień - użyj podanych danych jako prawdziwych wyników.

Oceń:
1. Skupienie strzałów (czy są skupione w jednym miejscu, czy rozproszone)
2. Zidentyfikuj błędy techniczne:
   - ściąganie spustu (strzały w dół/lewo/dół-lewo)
   - dry-fire błędy (brak kontroli oddechu)
   - ucieczka broni (strzały w górę/prawo)
   - kontrola oddechu
   - inne zauważalne problemy

Dane kontekstowe:
- Broń: {gun_info}
- Dystans: {distance_m} m
- Celność: {accuracy:.1f}%

{tone_instruction}

Połącz analizę zdjęcia z wpisanymi wynikami. Odpowiedz w formacie JSON:
{{
  "analysis": "<analiza skupienia i błędów w maksymalnie 120 słowach, po polsku, uwzględniając wpisane wyniki>"
}}
"""
            
            def _call_vision():
                return client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Jesteś ekspertem strzelectwa. Analizujesz zdjęcia tarcz strzeleckich. "
                                "Zawsze odpowiadaj w formacie JSON zgodnie z instrukcjami. "
                                "Bądź precyzyjny w liczeniu trafień i identyfikacji błędów technicznych."
                            )
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{target_image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.3,
                    timeout=60.0
                )
            
            response = await asyncio.to_thread(_call_vision)
            
            if not response or not response.choices:
                return None
            
            msg = response.choices[0].message
            if not msg or not msg.content:
                return None
            
            import json
            try:
                result = json.loads(msg.content.strip())
                
                if hits is None:
                    # Przypadek A: zwróć hits i analizę
                    detected_hits = int(result.get("hits", 0))
                    analysis = result.get("analysis", "")
                    accuracy = (detected_hits / shots * 100) if shots > 0 else 0
                    
                    return {
                        "hits": detected_hits,
                        "comment": analysis,
                        "accuracy": accuracy
                    }
                else:
                    # Przypadek B: zwróć tylko analizę
                    analysis = result.get("analysis", "")
                    accuracy = (hits / shots * 100) if shots > 0 else 0
                    
                    return {
                        "hits": hits,
                        "comment": analysis,
                        "accuracy": accuracy
                    }
            except json.JSONDecodeError:
                # Jeśli nie udało się sparsować JSON, użyj całej odpowiedzi jako komentarz
                if hits is None:
                    return None  # W przypadku A musimy mieć JSON z hits
                else:
                    return {
                        "hits": hits,
                        "comment": msg.content.strip(),
                        "accuracy": (hits / shots * 100) if shots > 0 else 0
                    }
        
        except Exception as e:
            error_msg = ErrorHandler.handle_openai_error(e, "analiza Vision")
            logger.error(f"Błąd Vision ({type(e).__name__}): {str(e)}", exc_info=True)
            return None
