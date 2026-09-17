from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService
from app.services.tenant import TenantService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    tenant = TenantService.get_by_id(
        db,
        data.tenant_id,
    )

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant introuvable.",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=403,
            detail="Tenant inactif.",
        )

    try:
        password_hash = hash_password(data.password)

        return UserService.create(
            db=db,
            tenant_id=data.tenant_id,
            email=data.email,
            username=data.username,
            password_hash=password_hash,
            role=data.role,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )