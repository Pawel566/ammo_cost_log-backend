from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    user_id: str
    ai_mode: str
    theme: str
    distance_unit: str


class UserSettingsUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ai_mode: Optional[str] = Field(default=None, max_length=20)
    theme: Optional[str] = Field(default=None, max_length=20)
    distance_unit: Optional[str] = Field(default=None, max_length=2)

