import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SyncOperation(Base):
    __tablename__ = "sync_operations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        Identity(),
        nullable=False,
        unique=True,
        index=True,
    )

    node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    
    tenant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    operation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )