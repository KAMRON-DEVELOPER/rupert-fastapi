from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from src.apps.users.models import (
        ResumeModel,
        ResumeSkillLink,
        UserModel,
        UserSkillLink,
    )
    from src.apps.vacancies.models import VacancyModel, VacancySkillLink


class SkillModel(BaseModel):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(
        String(length=64), unique=True, index=True
    )

    # Relationships
    user_links: Mapped[list[UserSkillLink]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    users: Mapped[list[UserModel]] = relationship(
        secondary="user_skill_links", back_populates="skills", viewonly=True
    )

    resume_links: Mapped[list[ResumeSkillLink]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    resumes: Mapped[list[ResumeModel]] = relationship(
        secondary="resume_skill_links", back_populates="skills", viewonly=True
    )

    vacancy_links: Mapped[list[VacancySkillLink]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    vacancies: Mapped[list[VacancyModel]] = relationship(
        secondary="vacancy_skill_links", back_populates="skills", viewonly=True
    )

    def __repr__(self):
        return f"<SkillModel {self.name}>"
