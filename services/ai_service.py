from typing import Optional, Dict, Any, List
from models import Gun, Attachment, Maintenance, User, ShootingSession, AccuracySession
from services.user_context import UserContext
from openai import OpenAI
import asyncio
import logging
from services.error_handler import ErrorHandler
from settings import settings

logger = logging.getLogger(__name__)


class AIService:
    @staticmethod
    async def analyze_weapon(
        gun: Gun,
        attachments: List[Attachment],
        maintenance: List[Maintenance],
        cost_sessions: List[ShootingSession],
        accuracy_sessions: List[AccuracySession],
        user_skill: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> str:
        api_key = api_key or settings.openai_api_key
        if not api_key:
            return "Brak klucza API OpenAI — dodaj klucz w formularzu aby otrzymać analizę AI."
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            return ErrorHandler.handle_openai_error(e, "openai_client_init")
        attachments_info = ", ".join([f"{att.name} ({att.type})" for att in attachments]) if attachments else "Brak"
        sorted_maintenance = sorted(maintenance, key=lambda x: x.date, reverse=True) if maintenance else []
        last_maintenance = sorted_maintenance[0] if sorted_maintenance else None
        maintenance_info = f"Ostatnia konserwacja: {last_maintenance.date}, {last_maintenance.rounds_since_last} strzałów od poprzedniej" if last_maintenance else "Brak konserwacji"
        total_shots = sum(s.shots for s in cost_sessions) + sum(s.shots for s in accuracy_sessions)
        avg_accuracy = None
        if accuracy_sessions:
            total_hits = sum(s.hits for s in accuracy_sessions)
            total_acc_shots = sum(s.shots for s in accuracy_sessions)
            if total_acc_shots > 0:
                avg_accuracy = (total_hits / total_acc_shots) * 100
        skill_info = f"Poziom zaawansowania: {user_skill}" if user_skill else "Poziom zaawansowania: nieokreślony"
        prompt = (
            f"Analiza broni strzeleckiej:\n"
            f"Broń: {gun.name}, kaliber {gun.caliber or 'nieokreślony'}, typ {gun.type or 'nieokreślony'}\n"
            f"{skill_info}\n"
            f"Wyposażenie: {attachments_info}\n"
            f"{maintenance_info}\n"
            f"Całkowita liczba strzałów: {total_shots}\n"
            f"{f'Średnia celność: {avg_accuracy:.1f}%' if avg_accuracy is not None else 'Brak danych o celności'}\n"
            f"Napisz kompleksową analizę po polsku (3-5 zdań) uwzględniającą:\n"
            f"- Stan techniczny broni na podstawie konserwacji\n"
            f"- Wpływ wyposażenia na możliwości\n"
            f"- Sugestie poprawy wyników\n"
            f"- Rekomendacje dotyczące konserwacji"
        )
        messages = [
            {"role": "system", "content": "Jesteś ekspertem od broni strzeleckiej i instruktorem strzelectwa."},
            {"role": "user", "content": prompt}
        ]
        try:
            def _create_completion():
                return client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
            response = await asyncio.to_thread(_create_completion)
            result = response.choices[0].message.content.strip()
            logger.info(f"Otrzymano analizę AI dla broni {gun.name}")
            return result
        except Exception as e:
            return ErrorHandler.handle_openai_error(e, "analyze_weapon")

