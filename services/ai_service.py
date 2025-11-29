import json
import asyncio
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from settings import settings
from models import Gun
from services.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class AIService:

   
    @staticmethod
    def _get_skill_level_tone(skill_level: str, accuracy: float) -> str:
        skill_level = (skill_level or "beginner").lower()
        is_good = accuracy >= 70
        is_poor = accuracy < 50

        if skill_level in ["beginner", "początkujący"]:
            return (
                "TON: bardzo łagodny, motywujący i wspierający. "
                "Brak sarkazmu. Krótko i delikatnie nazwij błędy."
            )

        if skill_level in ["intermediate", "średniozaawansowany"]:
            if is_poor:
                return "TON: konstruktywny i techniczny. Jedna uwaga + jedna poprawka."
            elif is_good:
                return "TON: profesjonalny i zbalansowany."
            return "TON: neutralny i rzeczowy."

        # Advanced
        if skill_level in ["advanced", "zaawansowany", "expert", "ekspert"]:
            if is_poor:
                return (
                    "TON: bezpośredni, twardy i sarkastyczny, ale konstruktywny. "
                    "Możesz zaznaczyć, że wynik wygląda komicznie jak na zawodowca."
                )
            return "TON: techniczny i bardzo precyzyjny."

        return "TON: profesjonalny."


    
    @staticmethod
    async def analyze_target_with_vision(
        gun: Gun,
        distance_m: float,
        shots: int,
        hits: Optional[int] = None,
        target_image_base64: Optional[str] = None,
        skill_level: str = "beginner",
        api_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        api_key = api_key or settings.openai_api_key
        if not api_key or len(api_key) < 10:
            logger.error("Brak lub nieprawidłowy klucz API")
            return None

        if not target_image_base64:
            return None

        if not distance_m or not shots:
            return None

        client = OpenAI(api_key=api_key)

       
        gun_info = gun.name
        if gun.type:
            gun_info += f", typ: {gun.type}"
        if gun.caliber:
            gun_info += f", kaliber: {gun.caliber}"

        # ---------------------------
        # PROMPT
        # ---------------------------
        if hits is None:
            # ---------------------------------------------------------------
            # Tryb A – Vision liczy trafienia
            # ---------------------------------------------------------------
            prompt = f"""
Twoim zadaniem jest analiza tarczy strzeleckiej na obrazie.

WYMAGANIA:
1. POLICZ DOKŁADNIE liczbę trafień (dziur)
2. Oceń skupienie
3. Oceń błędy techniczne: ściąganie spustu, uciekanie broni, kontrola oddechu
4. Użyj TYLKO JSON. BEZ dodatkowego tekstu.

KONTEXT:
Broń: {gun_info}
Dystans: {distance_m} m
Strzałów oddano: {shots}

{AIService._get_skill_level_tone(skill_level, 0)}

FORMAT ODPOWIEDZI (ZWROC TYLKO JSON, NIC WIĘCEJ):
{{
  "hits": <liczba>,
  "analysis": "<krótka analiza max 120 słów po polsku>"
}}
"""
        else:
           
            accuracy = (hits / shots * 100) if shots > 0 else 0

            prompt = f"""
Analizujesz tarczę strzelecką. NIE licz trafień — użyj danych podanych przez użytkownika.

DANE:
Broń: {gun_info}
Dystans: {distance_m} m
Trafienia: {hits}/{shots}
Celność: {accuracy:.1f}%

{AIService._get_skill_level_tone(skill_level, accuracy)}

ZADANIA:
1. Oceń skupienie
2. Oceń błędy techniczne (ściąganie spustu, oddech, odrzut)
3. Połącz analizę zdjęcia z wynikiem wpisanym przez użytkownika
4. Użyj TYLKO JSON.

FORMAT:
{{
  "analysis": "<krótka analiza max 120 słów po polsku>"
}}
"""

       
        def _call_vision():
            return client.chat.completions.create(
                model="gpt-4o",
                max_tokens=900,         # stabilne
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Zwracaj TYLKO czysty JSON. "
                            "Nigdy nie dodawaj wyjaśnień, nagłówków ani komentarzy."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{target_image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )

        try:
            response = await asyncio.to_thread(_call_vision)
            raw = response.choices[0].message.content.strip()

            logger.debug(f"VISION RAW: {raw[:200]}...")

            
            first = raw.find("{")
            last = raw.rfind("}") + 1
            raw_json = raw[first:last]

            data = json.loads(raw_json)

        
            if hits is None:
                detected_hits = int(data.get("hits", 0))
                accuracy = (detected_hits / shots * 100) if shots > 0 else 0

                return {
                    "hits": detected_hits,
                    "accuracy": accuracy,
                    "comment": data.get("analysis", "")
                }

            
            accuracy = (hits / shots * 100) if shots > 0 else 0

            return {
                "hits": hits,
                "accuracy": accuracy,
                "comment": data.get("analysis", "")
            }

        except Exception as e:
            logger.error(f"Vision error: {e}", exc_info=True)
            return None
