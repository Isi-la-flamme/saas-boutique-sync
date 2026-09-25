from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1,
    )

    last_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )