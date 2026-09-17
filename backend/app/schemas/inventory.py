from uuid import UUID

from pydantic import BaseModel, Field


class InventoryMovementCreate(BaseModel):
    product_id: UUID
    type: str = Field(pattern="^(in|out)$")
    quantity: int = Field(gt=0)


class InventoryMovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    type: str
    quantity: int

    model_config = {
        "from_attributes": True
    }