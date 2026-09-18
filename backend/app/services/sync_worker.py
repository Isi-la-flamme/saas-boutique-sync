import asyncio
import json

import httpx

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.sync_outbox import SyncOutbox
from app.models.tenant import Tenant


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

        print("🛑 Sync worker arrêté")

    async def _loop(self):
        while self.running:
            try:
                await self.process_pending()
            except Exception as exc:
                print(f"⚠️ Erreur sync : {exc}")

            await asyncio.sleep(5)

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

            sync_url = "http://127.0.0.1:8000/sync"

            response = await self._send_operation(
                sync_url,
                operation,
                payload,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Serveur sync HTTP {response.status_code}: "
                    f"{response.text}"
                )

            operation.synced = True
            db.commit()

            print("✅ Opération synchronisée")


        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

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