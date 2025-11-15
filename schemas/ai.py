from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    gun_id: str
    openai_api_key: Optional[str] = Field(default=None)

