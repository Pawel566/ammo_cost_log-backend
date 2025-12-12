from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class GunBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=20)
    type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class GunCreate(GunBase):
    created_at: Optional[date] = Field(default=None)

    @field_validator('created_at')
    @classmethod
    def validate_created_at(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError('created_at cannot be in the future')
        return v


class GunRead(GunBase):
    id: str
    user_id: str
    image_path: Optional[str] = None
    created_at: date

    model_config = ConfigDict(from_attributes=True)











