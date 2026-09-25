import asyncio
import json
import os

import httpx
from dotenv import load_dotenv
from sqlalchemy import select
from uuid import UUID

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.sync_outbox import SyncOutbox
from app.models.inventory import InventoryMovement
from app.models.sync_state import SyncState
from app.models.sale import Sale, SaleItem


load_dotenv()

SYNC_SERVER_URL = os.getenv("SYNC_SERVER_URL")

if not SYNC_SERVER_URL:
    raise RuntimeError(
        "SYNC_SERVER_URL doit être défini dans le fichier .env"
    )


class SyncWorker:

    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._loop())

        print("🔄 Sync worker démarré")

    async def stop(self):
        self.running = False

        if self.task:
            self.task.cancel()

            try:
                await self.task
            except asyncio.CancelledError:
                pass

            self.task = None

        print("🛑 Sync worker arrêté")

    async def _loop(self):
        while self.running:
            try:
                await self.process_pending()
                await self.process_pull()

            except Exception as exc:
                print(f"⚠️ Erreur sync : {exc}")

            await asyncio.sleep(5)

    # =========================================================
    # LOCAL → CENTRAL
    # =========================================================

    async def process_pending(self):
        db = SessionLocal()

        try:
            operation = db.scalar(
                select(SyncOutbox)
                .where(SyncOutbox.synced.is_(False))
                .order_by(SyncOutbox.created_at.asc())
                .limit(1)
            )

            if not operation:
                return

            print(
                f"📤 Synchronisation : "
                f"{operation.entity}/{operation.operation} "
                f"{operation.entity_id}"
            )

            payload = json.loads(operation.payload)

            sync_url = f"{SYNC_SERVER_URL}/sync"

            response = await self._send_operation(
                sync_url,
                operation,
                payload,
            )

            if response.status_code == 200:
                operation.synced = True
                db.commit()

                print("✅ Opération synchronisée")
                return

            if 500 <= response.status_code < 600:
                raise RuntimeError(
                    f"Serveur sync HTTP {response.status_code}"
                )

            if 400 <= response.status_code < 500:
                print(
                    f"❌ Erreur client HTTP {response.status_code} : "
                    f"{response.text}"
                )
                return

            raise RuntimeError(
                f"Réponse sync inattendue HTTP {response.status_code}"
            )

        except httpx.RequestError as exc:
            db.rollback()
            print(f"🌐 Réseau indisponible : {exc}")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    # =========================================================
    # CENTRAL → LOCAL
    # =========================================================

    async def process_pull(self):
        db = SessionLocal()

        try:
            state = db.get(SyncState, 1)

            if not state:
                state = SyncState(
                    id=1,
                    last_sequence=0,
                )

                db.add(state)
                db.commit()
                db.refresh(state)

            last_sequence = state.last_sequence

            tenant_id = os.getenv("TENANT_ID")

            if not tenant_id:
                raise RuntimeError("TENANT_ID doit être défini dans le fichier .env")

            if not tenant_id:
                return

            pull_url = f"{SYNC_SERVER_URL}/sync/pull"

            params = {
                "tenant_id": str(tenant_id),
                "after": last_sequence,
            }

            response = await self._pull_operations(
                pull_url,
                params,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Pull HTTP {response.status_code}: "
                    f"{response.text}"
                )

            data = response.json()
            operations = data.get("operations", [])

            if not operations:
                return

            print(
                f"📥 Pull central : "
                f"{len(operations)} opération(s)"
            )

            for operation in operations:
                await self._apply_operation(
                    db,
                    operation,
                )

                state.last_sequence = operation["sequence"]

            db.commit()

            print(
                f"✅ Pull terminé — "
                f"last_sequence={state.last_sequence}"
            )

        except httpx.RequestError as exc:
            db.rollback()
            print(f"🌐 Pull réseau indisponible : {exc}")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    async def _pull_operations(
        self,
        pull_url,
        params,
    ):
        async with httpx.AsyncClient(timeout=10) as client:
            return await client.get(
                pull_url,
                params=params,
            )

    async def _apply_operation(self, db, operation):
        entity = operation["entity"]
        action = operation["operation"]
        payload = operation["payload"]

        if entity == "product" and action == "create":
            product_id = UUID(payload["product_id"])
            tenant_id = UUID(payload["tenant_id"])

            existing = db.scalar(
                select(Product).where(
                    Product.id == product_id,
                    Product.tenant_id == tenant_id,
                )
            )

            if existing:
                print(f"⏭️ Produit déjà présent : {product_id}")
                return

            product = Product(
                id=product_id,
                tenant_id=tenant_id,
                name=payload["name"],
                price=payload["price"],
                stock=payload.get("stock", 0),
            )

            db.add(product)

            print(f"📦 Produit reçu du central : {payload['name']}")
            return

        if entity == "inventory_movement" and action == "create":
            movement_id = UUID(payload["movement_id"])
            tenant_id = UUID(payload["tenant_id"])
            product_id = UUID(payload["product_id"])

            existing = db.scalar(
                select(InventoryMovement).where(
                    InventoryMovement.id == movement_id,
                    InventoryMovement.tenant_id == tenant_id,
                )
            )

            if existing:
                print(f"⏭️ Mouvement déjà présent : {movement_id}")
                return

            movement = InventoryMovement(
                id=movement_id,
                tenant_id=tenant_id,
                product_id=product_id,
                type=payload["type"],
                quantity=payload["quantity"],
            )

            db.add(movement)

            print(f"📦 Mouvement reçu du central : {movement_id}")
            return

        if entity == "sale" and action == "create":
            sale_id = UUID(payload["sale_id"])
            tenant_id = UUID(payload["tenant_id"])

            existing = db.scalar(
                select(Sale).where(
                    Sale.id == sale_id,
                    Sale.tenant_id == tenant_id,
                )
            )

            if existing:
                print(f"⏭️ Vente déjà présente : {sale_id}")
                return

            sale = Sale(
                id=sale_id,
                tenant_id=tenant_id,
                total=payload["total"],
            )

            db.add(sale)
            db.flush()

            for item in payload["items"]:
                sale_item = SaleItem(
                    sale_id=sale_id,
                    product_id=UUID(item["product_id"]),
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"],
                )
                db.add(sale_item)

            print(f"🧾 Vente reçue du central : {sale_id}")
            return

        raise RuntimeError(
            f"Opération Pull non supportée : {entity}/{action}"
        )

    # =========================================================
    # HTTP PUSH
    # =========================================================

    async def _send_operation(
        self,
        sync_url,
        operation,
        payload,
    ):
        data = {
            "entity": operation.entity,
            "operation": operation.operation,
            "tenant_id": str(operation.tenant_id),
            "entity_id": str(operation.entity_id),
            "payload": payload,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            return await client.post(
                sync_url,
                json=data,
            )


sync_worker = SyncWorker()