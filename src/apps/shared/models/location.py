from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class BaseLocationModel(BaseModel):
    __abstract__ = True

    country_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("countries.id"),
        index=True,
    )
    city_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id"),
        index=True,
    )


class BaseNullableLocationModel(BaseModel):
    __abstract__ = True

    country_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("countries.id"),
        index=True,
    )
    city_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id"),
        index=True,
    )


class CountryModel(BaseModel):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(56), unique=True, index=True)

    def __repr__(self):
        return f"<CountryModel {self.name}>"


class CityModel(BaseModel):
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("country_id", "name", name="uq_city_name_country_id"),
    )

    country_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("countries.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(168), index=True)

    def __repr__(self):
        return f"<CityModel {self.name}>"
