from pydantic import BaseModel, Field, ConfigDict


class UserSettingsRead(BaseModel):
    user_id: str
    ai_mode: str
    theme: str
    distance_unit: str

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdate(BaseModel):
    ai_mode: Optional[str] = Field(default=None, max_length=20)
    theme: Optional[str] = Field(default=None, max_length=20)
    distance_unit: Optional[str] = Field(default=None, max_length=2)

