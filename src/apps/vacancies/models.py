from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.models import BaseModel, BaseNullableLocationModel
from src.apps.shared.schemas.enums import (
    ApplicationStatus,
    EmploymentType,
    PaymentFrequency,
    ProficiencyLevel,
    SalaryCurrency,
    Specialization,
    SubmissionType,
    VacancyStatus,
    WorkFormat,
)

if TYPE_CHECKING:
    from src.apps.companies.models import CompanyModel
    from src.apps.shared.models import SkillModel
    from src.apps.users.models import ResumeModel, UserModel


class VacancySkillLink(BaseModel):
    __tablename__ = "vacancy_skill_links"
    __table_args__ = (
        UniqueConstraint("vacancy_id", "skill_id", name="uq_vacancy_skill"),
    )

    vacancy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vacancies.id", ondelete="CASCADE")
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE")
    )
    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel, name="proficiency_level"), nullable=False
    )
    years_of_experience_min: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 1)
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    vacancy: Mapped[VacancyModel] = relationship(back_populates="skill_links")
    skill: Mapped[SkillModel] = relationship(back_populates="vacancy_links")

    def __repr__(self):
        return "<VacancySkillLink>"


class VacancyModel(BaseNullableLocationModel):
    __tablename__ = "vacancies"
    __table_args__ = (
        CheckConstraint(
            "salary_min <= salary_max", name="chk_vacancy_salary_range"
        ),
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    external_apply_url: Mapped[str | None] = mapped_column(Text)
    submission_type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, name="submission_type"), nullable=False
    )
    specialization: Mapped[Specialization] = mapped_column(
        Enum(Specialization, name="specialization"), index=True, nullable=False
    )
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[SalaryCurrency | None] = mapped_column(
        Enum(SalaryCurrency, name="salary_currency")
    )
    payment_frequency: Mapped[PaymentFrequency | None] = mapped_column(
        Enum(PaymentFrequency, name="payment_frequency")
    )
    years_of_experience_min: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 1)
    )
    work_format: Mapped[WorkFormat] = mapped_column(
        Enum(WorkFormat, name="work_format"),
        default=WorkFormat.onsite,
        nullable=False,
    )
    work_hours_per_week: Mapped[int | None] = mapped_column(SmallInteger)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type"),
        default=EmploymentType.full_time,
        nullable=False,
    )
    status: Mapped[VacancyStatus] = mapped_column(
        Enum(VacancyStatus, name="vacancy_status"),
        default=VacancyStatus.draft,
        nullable=False,
    )
    # Relationships
    company: Mapped[CompanyModel] = relationship(back_populates="vacancies")
    skill_links: Mapped[list[VacancySkillLink]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )
    skills: Mapped[list[SkillModel]] = relationship(
        secondary="vacancy_skill_links",
        back_populates="vacancies",
        viewonly=True,
    )
    applications: Mapped[list[ApplicationModel]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )
    saved_vacancies: Mapped[list[SavedVacancyModel]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )
    # Non-mapped attributes
    is_saved: bool | None = None
    has_applied: bool | None = None

    def __repr__(self):
        return f"<VacancyModel {self.title}>"


class ApplicationModel(BaseModel):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("applicant_id", "vacancy_id", name="uq_application"),
    )

    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL")
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.pending,
    )
    recruiter_note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    applicant: Mapped[UserModel] = relationship(back_populates="applications")
    resume: Mapped[ResumeModel | None] = relationship(
        back_populates="applications"
    )
    vacancy: Mapped[VacancyModel] = relationship(back_populates="applications")

    def __repr__(self):
        return "<ApplicationModel>"


class SavedVacancyModel(BaseModel):
    __tablename__ = "saved_vacancies"
    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_saved_vacancy"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="saved_vacancies")
    vacancy: Mapped[VacancyModel] = relationship(
        back_populates="saved_vacancies"
    )

    def __repr__(self):
        return "<SavedVacancyModel>"
