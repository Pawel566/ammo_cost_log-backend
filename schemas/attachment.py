from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from models import AttachmentType


class AttachmentCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)


class AttachmentRead(AttachmentCreate):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: str
    gun_id: str
    user_id: str
    added_at: datetime
    expires_at: Optional[datetime] = Field(default=None)


