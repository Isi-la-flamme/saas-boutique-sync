import json

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.sync_operation import SyncOperation
from app.models.sale import Sale, SaleItem
from app.models.inventory import InventoryMovement
from app.models.product import Product


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Saas-Boutique Central",
    version="0.1.0",
)


@app.get("/health")
def health(
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "error",
            "database": "disconnected",
        }


@app.post("/sync")
def receive_sync(
    operation: dict,
    db: Session = Depends(get_db),
):
    required = [
        "entity",
        "operation",
        "tenant_id",
        "entity_id",
        "payload",
    ]

    if not all(operation.get(key) for key in required):
        raise HTTPException(
            status_code=400,
            detail="Invalid synchronization payload",
        )

    entity = operation["entity"]
    action = operation["operation"]
    tenant_id = str(operation["tenant_id"])
    entity_id = str(operation["entity_id"])
    payload = operation["payload"]

    # 1. Idempotence
    existing = db.query(SyncOperation).filter(
        SyncOperation.entity == entity,
        SyncOperation.operation == action,
        SyncOperation.entity_id == entity_id,
        SyncOperation.tenant_id == tenant_id,
    ).first()

    if existing:
        return {
            "status": "already_processed",
            "operation_id": str(existing.id),
        }

    # 2. Synchronisation d'un produit
    if entity == "product" and action == "create":
        product_id = str(payload["product_id"])

        existing_product = db.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        ).first()

        if not existing_product:
            product = Product(
                id=product_id,
                tenant_id=tenant_id,
                name=payload["name"],
                price=payload["price"],
                stock=payload.get("stock", 0),
            )

            db.add(product)

    # 3. Synchronisation d'un mouvement de stock
    elif entity == "inventory_movement" and action == "create":
        movement_id = str(payload["movement_id"])
        product_id = str(payload["product_id"])
        movement_type = payload["type"]
        quantity = int(payload["quantity"])

        product = db.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Produit introuvable au central.",
            )

        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="La quantité doit être supérieure à zéro.",
            )

        if movement_type == "in":
            product.stock += quantity

        elif movement_type == "out":
            if product.stock < quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Stock central insuffisant.",
                )

            product.stock -= quantity

        else:
            raise HTTPException(
                status_code=400,
                detail="Type de mouvement invalide.",
            )

        movement = InventoryMovement(
            id=movement_id,
            tenant_id=tenant_id,
            product_id=product_id,
            type=movement_type,
            quantity=quantity,
        )

        db.add(movement)

    # 4. Synchronisation d'une vente
    elif entity == "sale" and action == "create":
        sale_id = str(payload["sale_id"])

        existing_sale = db.query(Sale).filter(
            Sale.id == sale_id,
            Sale.tenant_id == tenant_id,
        ).first()

        if not existing_sale:
            sale = Sale(
                id=sale_id,
                tenant_id=tenant_id,
                total=payload["total"],
            )

            db.add(sale)

            for item in payload["items"]:
                product_id = str(item["product_id"])
                quantity = int(item["quantity"])

                product = db.query(Product).filter(
                    Product.id == product_id,
                    Product.tenant_id == tenant_id,
                ).first()

                if not product:
                    raise HTTPException(
                        status_code=404,
                        detail="Produit de la vente introuvable.",
                    )

                if product.stock < quantity:
                    raise HTTPException(
                        status_code=400,
                        detail="Stock central insuffisant.",
                    )

                product.stock -= quantity

                sale_item = SaleItem(
                    sale_id=sale_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"],
                )

                db.add(sale_item)

                movement = InventoryMovement(
                    tenant_id=tenant_id,
                    product_id=product_id,
                    type="out",
                    quantity=quantity,
                )

                db.add(movement)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Synchronisation non supportée : {entity}/{action}",
        )

    # 5. Enregistrer l'opération reçue
    sync_operation = SyncOperation(
        tenant_id=tenant_id,
        operation=action,
        entity=entity,
        entity_id=entity_id,
        payload=json.dumps(payload),
    )

    db.add(sync_operation)

    try:
        db.commit()
        db.refresh(sync_operation)

    except Exception:
        db.rollback()
        raise

    print(
        f"📥 Central sync : "
        f"{entity}/{action} "
        f"{entity_id}"
    )

    return {
        "status": "accepted",
        "operation_id": str(sync_operation.id),
    }


@app.get("/sync/pull")
def pull_sync(
    tenant_id: str,
    after: int = 0,
    db: Session = Depends(get_db),
):
    operations = (
        db.query(SyncOperation)
        .filter(
            SyncOperation.tenant_id == tenant_id,
            SyncOperation.sequence > after,
        )
        .order_by(SyncOperation.sequence.asc())
        .limit(100)
        .all()
    )

    return {
        "operations": [
            {
                "sequence": operation.sequence,
                "entity": operation.entity,
                "operation": operation.operation,
                "tenant_id": operation.tenant_id,
                "entity_id": operation.entity_id,
                "payload": json.loads(operation.payload),
            }
            for operation in operations
        ],
        "next_sequence": (
            operations[-1].sequence
            if operations
            else after
        ),
    }