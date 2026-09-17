from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sale import SaleService


router = APIRouter(
    prefix="/sales",
    tags=["POS"],
)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=201,
)
def create_sale(
    data: SaleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return SaleService.create(
            db=db,
            tenant_id=UUID(current_user["tenant_id"]),
            items=data.items,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )