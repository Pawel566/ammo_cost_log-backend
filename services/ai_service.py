from typing import Optional, Dict, Any
from models import Gun, Attachment, Maintenance, User
from services.user_context import UserContext


class AIService:
    @staticmethod
    async def analyze_weapon(
        gun: Gun,
        attachments: list[Attachment],
        maintenance: list[Maintenance],
        user: UserContext,
        user_skill: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    @staticmethod
    async def analyze_sessions(
        sessions: list,
        gun: Gun,
        attachments: list[Attachment],
        maintenance: list[Maintenance],
        user: UserContext,
        user_skill: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

