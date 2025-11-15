from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class ChangeEmailRequest(BaseModel):
    new_email: str = Field(min_length=1)


class UpdateSkillLevelRequest(BaseModel):
    skill_level: str = Field(min_length=1)


class DeleteAccountRequest(BaseModel):
    password: str

