from datetime import date
from uuid import UUID

from src.apps.shared.schemas import BaseModelResponse, RequestSchema, SkillResponse
from src.apps.shared.schemas.enums import ProficiencyLevel


class ResumeSkillLinkRequest(RequestSchema):
    skill_id: UUID
    proficiency: ProficiencyLevel
    last_used_at: date | None = None


class ResumeSkillLinkResponse(BaseModelResponse):
    resume_id: UUID
    skill: SkillResponse
    proficiency: ProficiencyLevel
    last_used_at: date | None


class UserSkillLinkRequest(RequestSchema):
    skill_id: UUID
    proficiency: ProficiencyLevel
    last_used_at: date | None = None


class UserSkillLinkResponse(BaseModelResponse):
    skill: SkillResponse
    proficiency: ProficiencyLevel
    last_used_at: date | None
