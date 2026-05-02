from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class BaseLocationModel(BaseModel):
    __abstract__ = True

    country: Mapped[str] = mapped_column(String(64))
    city: Mapped[str] = mapped_column(String(64))


class BaseNullableLocationModel(BaseModel):
    __abstract__ = True

    country: Mapped[str | None] = mapped_column(String(64))
    city: Mapped[str | None] = mapped_column(String(64))
