from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    price: Decimal
    duration_minutes: int


class SessionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    description: str


class SessionDetailResponse(SessionListResponse):
    packages: list[PackageResponse]
