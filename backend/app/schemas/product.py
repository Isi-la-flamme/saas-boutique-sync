from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class ProductResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    price: Decimal
    stock: int
    is_active: bool

    model_config = {
        "from_attributes": True
    }