import json

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sync_outbox import SyncOutbox
from app.core.config import NODE_ID


class SyncOutboxService:

    @staticmethod
    def add(
        db: Session,
        tenant_id: UUID,
        operation: str,
        entity: str,
        entity_id: UUID,
        payload: dict,
    ) -> SyncOutbox:
        outbox = SyncOutbox(
            tenant_id=tenant_id,
            node_id=NODE_ID,
            operation=operation,
            entity=entity,
            entity_id=entity_id,
            payload=json.dumps(payload),
        )

        db.add(outbox)
        return outbox