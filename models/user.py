from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserBase(SQLModel):
    skill_level: str = Field(default="beginner", max_length=20)


class User(UserBase, table=True):
    __tablename__ = "users"
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)


class UserSettingsBase(SQLModel):
    ai_mode: str = Field(default="off", max_length=20)
    theme: str = Field(default="dark", max_length=20)
    distance_unit: str = Field(default="m", max_length=2)


class UserSettings(UserSettingsBase, table=True):
    __tablename__ = "user_settings"
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

