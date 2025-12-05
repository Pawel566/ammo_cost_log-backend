from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserSettingsRead(BaseModel):
    user_id: str
    ai_mode: str
    theme: str
    distance_unit: str
    maintenance_rounds_limit: int
    maintenance_days_limit: int
    maintenance_notifications_enabled: bool
    low_ammo_notifications_enabled: bool
    ai_analysis_intensity: str
    ai_auto_comments: bool
    language: str = "pl"
    currency: str = "pln"

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    ai_mode: Optional[str] = Field(default=None, max_length=20)
    theme: Optional[str] = Field(default=None, max_length=20)
    distance_unit: Optional[str] = Field(default=None, max_length=2)
    maintenance_rounds_limit: Optional[int] = Field(default=None, ge=1)
    maintenance_days_limit: Optional[int] = Field(default=None, ge=1)
    maintenance_notifications_enabled: Optional[bool] = None
    low_ammo_notifications_enabled: Optional[bool] = None
    ai_analysis_intensity: Optional[str] = Field(default=None, max_length=20)
    ai_auto_comments: Optional[bool] = None
    language: Optional[str] = Field(default=None, max_length=10)
    currency: Optional[str] = Field(default=None, max_length=3)

