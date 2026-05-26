from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, func
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid4, primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )
