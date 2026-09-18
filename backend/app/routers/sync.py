from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sync_outbox import SyncOutbox

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("")
def receive_sync(
    operation: dict,
    db: Session = Depends(get_db),
):
    entity = operation.get("entity")
    action = operation.get("operation")
    tenant_id = operation.get("tenant_id")
    entity_id = operation.get("entity_id")
    payload = operation.get("payload")

    if not all([entity, action, tenant_id, entity_id, payload]):
        raise HTTPException(
            status_code=400,
            detail="Invalid synchronization payload",
        )

    print(
        f"📥 Sync reçue : "
        f"{entity}/{action} "
        f"tenant={tenant_id}"
    )

    # Pour l'instant on accuse réception.
    # Le traitement métier réel viendra juste après.
    return {
        "status": "accepted",
        "entity": entity,
        "entity_id": entity_id,
    }