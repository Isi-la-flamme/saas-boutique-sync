from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.services.sync_outbox import SyncOutboxService


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
        db.flush()

        SyncOutboxService.add(
            db=db,
            tenant_id=tenant_id,
            operation="create",
            entity="inventory_movement",
            entity_id=movement.id,
            payload={
                "movement_id": str(movement.id),
                "tenant_id": str(tenant_id),
                "product_id": str(product_id),
                "type": movement_type,
                "quantity": quantity,
            },
        )

        db.commit()
        db.refresh(movement)

        return movement