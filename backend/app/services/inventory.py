from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMovement
from app.models.product import Product


class InventoryService:

    @staticmethod
    def move(
        db: Session,
        tenant_id: UUID,
        product_id: UUID,
        movement_type: str,
        quantity: int,
    ) -> InventoryMovement:

        if movement_type not in ("in", "out"):
            raise ValueError("Type de mouvement invalide.")

        if quantity <= 0:
            raise ValueError("La quantité doit être supérieure à zéro.")

        product = db.scalar(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
                Product.is_active.is_(True),
            )
        )

        if not product:
            raise ValueError("Produit introuvable.")

        if movement_type == "out":
            if product.stock < quantity:
                raise ValueError("Stock insuffisant.")

            product.stock -= quantity

        else:
            product.stock += quantity

        movement = InventoryMovement(
            tenant_id=tenant_id,
            product_id=product_id,
            type=movement_type,
            quantity=quantity,
        )

        db.add(movement)
        db.commit()
        db.refresh(movement)

        return movement