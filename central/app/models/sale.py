import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    tenant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem",
        cascade="all, delete-orphan",
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    sale_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("sales.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )