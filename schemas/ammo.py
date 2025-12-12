from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from models import AmmoType, AmmoCategory


class AmmoCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=50)
    type: Optional[AmmoType] = Field(default=None)
    category: Optional[AmmoCategory] = Field(default=None)
    price_per_unit: float = Field(gt=0, le=1000000)  # Maksymalna cena: 1,000,000
    units_in_package: Optional[int] = Field(default=None, gt=0, le=1000000)  # Maksymalna ilość: 1,000,000


class AmmoRead(AmmoCreate):
    id: str
    user_id: str

    model_config = ConfigDict(from_attributes=True)











