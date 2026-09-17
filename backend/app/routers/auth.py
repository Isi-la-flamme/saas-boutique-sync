from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.user import UserService
from fastapi import APIRouter, Depends, HTTPException

from app.middlewares.auth import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = UserService.get_by_email(
        db=db,
        tenant_id=data.tenant_id,
        email=data.email,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Utilisateur inactif.",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides.",
        )

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )

    return LoginResponse(
        access_token=token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )

@router.get("/me")
def me(
    current_user: dict = Depends(get_current_user),
):
    return current_user