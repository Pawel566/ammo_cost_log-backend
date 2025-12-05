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
    def _get_skill_level_tone(skill_level: str, accuracy: float, language: str = "pl") -> str:
        skill_level = (skill_level or "beginner").lower()
        is_good = accuracy >= 70
        is_poor = accuracy < 50
        language = language or "pl"

        if language == "en":
            if skill_level in ["beginner", "początkujący"]:
                return (
                    "TONE: very gentle, motivating and supportive. "
                    "No sarcasm. Briefly and delicately name mistakes."
                )

            if skill_level in ["intermediate", "średniozaawansowany"]:
                if is_poor:
                    return "TONE: constructive and technical. One remark + one correction."
                elif is_good:
                    return "TONE: professional and balanced."
                return "TONE: neutral and factual."

            # Advanced
            if skill_level in ["advanced", "zaawansowany", "expert", "ekspert"]:
                if is_poor:
                    return (
                        "TONE: direct, tough and sarcastic, but constructive. "
                        "You can note that the result looks comical for a professional."
                    )
                return "TONE: technical and very precise."

            return "TONE: professional."
        else:
            # Polish (default)
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
        language: str = "pl",
        api_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        api_key = api_key or settings.openai_api_key
        logger.info(f"analyze_target_with_vision wywołane: gun={gun.name}, distance_m={distance_m}, shots={shots}, hits={hits}, has_image={bool(target_image_base64)}, skill_level={skill_level}")
        logger.info(f"API key dostępny: {bool(api_key)}, długość: {len(api_key) if api_key else 0}")
        if not api_key or len(api_key) < 10:
            logger.error("Brak lub nieprawidłowy klucz API")
            return None

        if not target_image_base64:
            logger.warning("Brak zdjęcia tarczy (target_image_base64)")
            return None

        if not distance_m or not shots:
            logger.warning(f"Brak wymaganych danych: distance_m={distance_m}, shots={shots}")
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
        language = language or "pl"
        language_name = "English" if language == "en" else "polsku"
        
        if hits is None:
            # ---------------------------------------------------------------
            # Tryb A – Vision liczy trafienia
            # ---------------------------------------------------------------
            if language == "en":
                prompt = f"""
Your task is to analyze a shooting target in the image.

REQUIREMENTS:
1. COUNT EXACTLY the number of hits (holes)
2. Assess grouping
3. Assess technical errors: trigger pull, gun movement, breath control
4. Use ONLY JSON. NO additional text.

CONTEXT:
Weapon: {gun_info}
Distance: {distance_m} m
Shots fired: {shots}

{AIService._get_skill_level_tone(skill_level, 0, language)}

RESPONSE FORMAT (RETURN ONLY JSON, NOTHING ELSE):
{{
  "hits": <number>,
  "analysis": "<short analysis max 120 words in English>"
}}
"""
            else:
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

{AIService._get_skill_level_tone(skill_level, 0, language)}

FORMAT ODPOWIEDZI (ZWROC TYLKO JSON, NIC WIĘCEJ):
{{
  "hits": <liczba>,
  "analysis": "<krótka analiza max 120 słów po {language_name}>"
}}
"""
        else:
           
            accuracy = (hits / shots * 100) if shots > 0 else 0

            if language == "en":
                prompt = f"""
You are analyzing a shooting target. DO NOT count hits — use data provided by the user.

DATA:
Weapon: {gun_info}
Distance: {distance_m} m
Hits: {hits}/{shots}
Accuracy: {accuracy:.1f}%

{AIService._get_skill_level_tone(skill_level, accuracy, language)}

TASKS:
1. Assess grouping
2. Assess technical errors (trigger pull, breathing, recoil)
3. Combine image analysis with the result entered by the user
4. Use ONLY JSON.

FORMAT:
{{
  "analysis": "<short analysis max 120 words in English>"
}}
"""
            else:
                prompt = f"""
Analizujesz tarczę strzelecką. NIE licz trafień — użyj danych podanych przez użytkownika.

DANE:
Broń: {gun_info}
Dystans: {distance_m} m
Trafienia: {hits}/{shots}
Celność: {accuracy:.1f}%

{AIService._get_skill_level_tone(skill_level, accuracy, language)}

ZADANIA:
1. Oceń skupienie
2. Oceń błędy techniczne (ściąganie spustu, oddech, odrzut)
3. Połącz analizę zdjęcia z wynikiem wpisanym przez użytkownika
4. Użyj TYLKO JSON.

FORMAT:
{{
  "analysis": "<krótka analiza max 120 słów po {language_name}>"
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
                            "Return ONLY clean JSON. "
                            "Never add explanations, headers or comments."
                        ) if language == "en" else (
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

    @staticmethod
    async def generate_comment(
        gun: Gun,
        distance_m: float,
        hits: int,
        shots: int,
        accuracy: float,
        skill_level: str = "beginner",
        language: str = "pl",
        api_key: Optional[str] = None
    ) -> str:
        """
        Generuje komentarz AI dla sesji strzeleckiej bez zdjęcia.
        Używa modelu gpt-4o-mini.
        """
        logger.info(f"generate_comment wywołane: gun={gun.name}, distance_m={distance_m}, hits={hits}, shots={shots}, accuracy={accuracy}, skill_level={skill_level}")
        api_key = api_key or settings.openai_api_key
        logger.info(f"API key dostępny: {bool(api_key)}, długość: {len(api_key) if api_key else 0}")
        if not api_key or len(api_key) < 10:
            logger.error("Brak lub nieprawidłowy klucz API")
            return "Brak klucza API OpenAI. Skonfiguruj OPENAI_API_KEY w zmiennych środowiskowych."

        client = OpenAI(api_key=api_key)

        gun_info = gun.name
        if gun.type:
            gun_info += f", typ: {gun.type}"
        if gun.caliber:
            gun_info += f", kaliber: {gun.caliber}"

        language = language or "pl"
        
        if language == "en":
            prompt = f"""
You are analyzing a shooting session. Evaluate the result and give constructive feedback.

DATA:
Weapon: {gun_info}
Distance: {distance_m} m
Hits: {hits}/{shots}
Accuracy: {accuracy:.1f}%

{AIService._get_skill_level_tone(skill_level, accuracy, language)}

TASKS:
1. Evaluate the result (accuracy, grouping)
2. Point out main technical errors (if any)
3. Give a short improvement tip (if needed)
4. Maximum 120 words in English
5. Be constructive and helpful

Return ONLY the comment, without additional headers or formatting.
"""
        else:
            prompt = f"""
Analizujesz sesję strzelecką. Oceń wynik i daj konstruktywny komentarz.

DANE:
Broń: {gun_info}
Dystans: {distance_m} m
Trafienia: {hits}/{shots}
Celność: {accuracy:.1f}%

{AIService._get_skill_level_tone(skill_level, accuracy, language)}

ZADANIA:
1. Oceń wynik (celność, skupienie)
2. Wskaż główne błędy techniczne (jeśli są)
3. Daj krótką wskazówkę do poprawy (jeśli potrzebna)
4. Maksymalnie 120 słów po polsku
5. Bądź konstruktywny i pomocny

Zwróć TYLKO komentarz, bez dodatkowych nagłówków ani formatowania.
"""

        def _call_api():
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=300,
                    temperature=0.7,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a shooting expert. You give short, constructive comments in English."
                                if language == "en"
                                else "Jesteś ekspertem strzeleckim. Dajesz krótkie, konstruktywne komentarze po polsku."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI API error: {e}", exc_info=True)
                raise

        try:
            comment = await asyncio.to_thread(_call_api)
            if not comment or len(comment) < 10:
                return "Błąd podczas generowania komentarza: odpowiedź z API jest pusta lub zbyt krótka."
            return comment
        except Exception as e:
            logger.error(f"Błąd podczas generowania komentarza: {e}", exc_info=True)
            error_msg = str(e)
            if "insufficient_quota" in error_msg.lower() or "billing" in error_msg.lower():
                return "Błąd podczas generowania komentarza: przekroczono limit lub brak środków na koncie OpenAI."
            elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return "Błąd podczas generowania komentarza: nieprawidłowy klucz API OpenAI."
            else:
                return f"Błąd podczas generowania komentarza: {error_msg}"
