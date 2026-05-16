from uuid import UUID

from src.apps.shared.schemas import (
    BaseModelResponse,
    RequestSchema,
    SkillResponse,
)
from src.apps.shared.schemas.enums import ProficiencyLevel


class VacancySkillLinkRequest(RequestSchema):
    skill_id: UUID
    proficiency: ProficiencyLevel
    years_of_experience_min: float | None = None
    is_required: bool = True


class VacancySkillLinkResponse(BaseModelResponse):
    skill: SkillResponse
    proficiency: ProficiencyLevel
    years_of_experience_min: float | None
    is_required: bool
