from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
)
def create_product(
    data: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProductService.create(
        db=db,
        tenant_id=UUID(current_user["tenant_id"]),
        name=data.name,
        price=data.price,
        stock=data.stock,
    )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProductService.get_all(
        db=db,
        tenant_id=UUID(current_user["tenant_id"]),
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = ProductService.get_by_id(
        db=db,
        tenant_id=UUID(current_user["tenant_id"]),
        product_id=product_id,
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable.",
        )

    return product