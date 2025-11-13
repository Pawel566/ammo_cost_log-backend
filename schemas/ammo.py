from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AmmoCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=20)
    price_per_unit: float = Field(gt=0)
    units_in_package: Optional[int] = Field(default=None, gt=0)


class AmmoRead(AmmoCreate):
    id: int
    user_id: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)








