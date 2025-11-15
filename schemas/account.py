from pydantic import BaseModel, Field, ConfigDict


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    old_password: str
    new_password: str = Field(min_length=6)


class ChangeEmailRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    new_email: str = Field(min_length=1)


class UpdateSkillLevelRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    skill_level: str = Field(min_length=1)


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    password: str

