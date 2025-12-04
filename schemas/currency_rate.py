from pydantic import BaseModel, ConfigDict
from datetime import date as Date
from typing import Optional


class CurrencyRateRead(BaseModel):
    id: int
    code: str
    rate: float
    date: Date

    model_config = ConfigDict(from_attributes=True)


class CurrencyRateCreate(BaseModel):
    code: str
    rate: float
    date: Date

