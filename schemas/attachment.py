from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from models.attachment import AttachmentType


class AttachmentCreate(BaseModel):
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)


class AttachmentRead(AttachmentCreate):
    id: str
    gun_id: str
    user_id: str
    added_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


