from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services.tenant import TenantService


router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
)


@router.post(
    "",
    response_model=TenantResponse,
    status_code=201,
)
def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
):
    try:
        return TenantService.create(
            db=db,
            name=data.name,
            slug=data.slug,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
):
    tenant = TenantService.get_by_id(db, tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant introuvable.",
        )

    return tenant