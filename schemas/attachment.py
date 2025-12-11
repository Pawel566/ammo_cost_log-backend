from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from models import AttachmentType


class AttachmentCreate(BaseModel):
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    precision_help: str = Field(default="none", max_length=20, pattern="^(none|low|medium|high)$")
    recoil_reduction: str = Field(default="none", max_length=20, pattern="^(none|low|medium|high)$")
    ergonomics: str = Field(default="none", max_length=20, pattern="^(none|low|medium|high)$")


class AttachmentRead(AttachmentCreate):
    id: str
    gun_id: str
    user_id: str
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


