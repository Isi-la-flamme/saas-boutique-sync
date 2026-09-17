from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.inventory import (
    InventoryMovementCreate,
    InventoryMovementResponse,
)
from app.services.inventory import InventoryService


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


@router.post(
    "/movement",
    response_model=InventoryMovementResponse,
    status_code=201,
)
def create_movement(
    data: InventoryMovementCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return InventoryService.move(
            db=db,
            tenant_id=UUID(current_user["tenant_id"]),
            product_id=data.product_id,
            movement_type=data.type,
            quantity=data.quantity,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )