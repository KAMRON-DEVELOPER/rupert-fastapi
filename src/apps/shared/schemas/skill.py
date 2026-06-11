from datetime import date
from uuid import UUID

from pydantic import Field

from src.apps.shared.schemas.enums import ProficiencyLevel

from .base import BaseModelResponse, RequestSchema


class SkillRequest(RequestSchema):
    name: str = Field(max_length=64)


class SkillResponse(BaseModelResponse):
    name: str


class SkillLinkCreateRequest(RequestSchema):
    skill_id: UUID
    proficiency: ProficiencyLevel
    last_used_at: date | None = None


class SkillLinkUpdateRequest(RequestSchema):
    id: UUID
    skill_id: UUID
    proficiency: ProficiencyLevel | None = None
    last_used_at: date | None = None


class SkillLinkBatchCreateRequest(RequestSchema):
    skills: list[SkillLinkCreateRequest]


class SkillLinkBatchUpdateRequest(RequestSchema):
    skills: list[SkillLinkUpdateRequest]


class SkillLinkBatchDeleteRequest(RequestSchema):
    skill_link_ids: list[UUID]


class SkillLinkResponse(BaseModelResponse):
    skill: SkillResponse
    proficiency: ProficiencyLevel
    last_used_at: date | None
