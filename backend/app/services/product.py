from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductService:

    @staticmethod
    def create(
        db: Session,
        tenant_id: UUID,
        name: str,
        price: float,
        stock: int = 0,
    ) -> Product:

        product = Product(
            tenant_id=tenant_id,
            name=name.strip(),
            price=price,
            stock=stock,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def get_all(
        db: Session,
        tenant_id: UUID,
    ) -> list[Product]:

        return list(
            db.scalars(
                select(Product)
                .where(
                    Product.tenant_id == tenant_id,
                    Product.is_active.is_(True),
                )
                .order_by(Product.created_at.desc())
            )
        )

    @staticmethod
    def get_by_id(
        db: Session,
        tenant_id: UUID,
        product_id: UUID,
    ) -> Product | None:

        return db.scalar(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
                Product.is_active.is_(True),
            )
        )