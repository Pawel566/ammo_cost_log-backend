from sqlmodel import SQLModel, Field
from datetime import date as Date
from typing import Optional


class CurrencyRateBase(SQLModel):
    code: str = Field(max_length=3, index=True)
    rate: float = Field(gt=0)
    date: Date


class CurrencyRate(CurrencyRateBase, table=True):
    __tablename__ = "currency_rates"
    id: Optional[int] = Field(default=None, primary_key=True)

