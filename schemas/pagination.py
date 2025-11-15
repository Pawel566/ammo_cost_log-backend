from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    total: int
    items: List[T]

