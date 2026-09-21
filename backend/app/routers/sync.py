from fastapi import APIRouter, Depends
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middlewares.auth import get_current_user
from app.models.sync_outbox import SyncOutbox


router = APIRouter(prefix="/sync", tags=["Sync"])


@router.get("/status")
def sync_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    tenant_id = UUID(current_user["tenant_id"])

    pending = db.scalar(
        select(func.count())
        .select_from(SyncOutbox)
        .where(
            SyncOutbox.tenant_id == tenant_id,
            SyncOutbox.synced.is_(False),
        )
    )

    synced = db.scalar(
        select(func.count())
        .select_from(SyncOutbox)
        .where(
            SyncOutbox.tenant_id == tenant_id,
            SyncOutbox.synced.is_(True),
        )
    )

    return {
        "pending": pending,
        "synced": synced,
        "total": pending + synced,
    }