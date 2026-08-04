from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.models import BaseLocationModel, BaseModel
from src.apps.shared.schemas import PermissionSchema
from src.apps.shared.schemas.enums import (
    CompanyMemberRole,
    CompanyStatus,
    CompanyType,
)

if TYPE_CHECKING:
    from src.apps.users.models import UserModel
    from src.apps.vacancies.models import VacancyModel


class CompanyMemberModel(BaseModel):
    __tablename__ = "company_members"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_company_member"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )
    role: Mapped[CompanyMemberRole] = mapped_column(
        Enum(CompanyMemberRole, name="company_member_role"),
        default=CompanyMemberRole.member,
    )

    user: Mapped[UserModel] = relationship(back_populates="company_memberships")
    company: Mapped[CompanyModel] = relationship(back_populates="members")

    def __repr__(self):
        return "<CompanyMemberModel>"


class CompanyModel(BaseLocationModel):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    tagline: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)
    type: Mapped[CompanyType] = mapped_column(
        Enum(CompanyType, name="company_type")
    )
    contact_email: Mapped[str | None] = mapped_column(String(128))
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status"),
        default=CompanyStatus.pending,
    )

    members: Mapped[list[CompanyMemberModel]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    vacancies: Mapped[list[VacancyModel]] = relationship(
        back_populates="company", passive_deletes=True
    )

    # Non-mapped attributes
    open_vacancies_count: int | None = None
    member_count: int | None = None
    permission: PermissionSchema | None = None

    def __repr__(self):
        return f"<CompanyModel {self.name}>"
