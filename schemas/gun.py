from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GunCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=20)
    type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class GunRead(GunCreate):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: str
    user_id: str
    expires_at: Optional[datetime] = Field(default=None)











