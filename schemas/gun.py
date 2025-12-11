from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GunCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=20)
    type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: Optional[date] = Field(default=None)


class GunRead(GunCreate):
    id: str
    user_id: str
    image_path: Optional[str] = None
    created_at: date

    model_config = ConfigDict(from_attributes=True)











