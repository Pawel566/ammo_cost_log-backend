from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from models import AmmoType, AmmoCategory


class AmmoBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, min_length=1, max_length=50)
    type: Optional[AmmoType] = Field(default=None)
    category: Optional[AmmoCategory] = Field(default=None)
    price_per_unit: float = Field(ge=0, le=1000000)
    units_in_package: Optional[int] = Field(default=None, ge=0, le=1000000)


class AmmoCreate(AmmoBase):
    pass


class AmmoRead(AmmoBase):
    id: str
    user_id: str

    model_config = ConfigDict(from_attributes=True)











