from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.services.sync_outbox import SyncOutboxService


class SaleService:

    @staticmethod
    def create(
        db: Session,
        tenant_id: UUID,
        items: list,
    ) -> Sale:

        with db.begin():

            sale_items = []
            total = Decimal("0.00")

            for item in items:

                product = db.scalar(
                    select(Product)
                    .where(
                        Product.id == item.product_id,
                        Product.tenant_id == tenant_id,
                        Product.is_active.is_(True),
                    )
                    .with_for_update()
                )

                if not product:
                    raise ValueError(
                        "Produit introuvable."
                    )

                if product.stock < item.quantity:
                    raise ValueError(
                        f"Stock insuffisant pour {product.name}."
                    )

                unit_price = Decimal(product.price)
                subtotal = unit_price * item.quantity

                product.stock -= item.quantity

                movement = InventoryMovement(
                    tenant_id=tenant_id,
                    product_id=product.id,
                    type="out",
                    quantity=item.quantity,
                )

                db.add(movement)

                sale_item = SaleItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )

                sale_items.append(sale_item)
                total += subtotal

            sale = Sale(
                tenant_id=tenant_id,
                total=total,
            )

            db.add(sale)
            db.flush()

            for item in sale_items:
                item.sale_id = sale.id
                db.add(item)

            db.flush()

            sale.items = sale_items

            # Ajout de l'opération à synchroniser
            SyncOutboxService.add(
                db=db,
                tenant_id=tenant_id,
                operation="create",
                entity="sale",
                entity_id=sale.id,
                payload={
                    "sale_id": str(sale.id),
                    "tenant_id": str(tenant_id),
                    "total": str(total),
                    "items": [
                        {
                            "product_id": str(item.product_id),
                            "quantity": item.quantity,
                            "unit_price": str(item.unit_price),
                            "subtotal": str(item.subtotal),
                        }
                        for item in sale_items
                    ],
                },
            )

        return sale