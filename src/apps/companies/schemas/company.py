from uuid import UUID

from fastapi import Query
from pydantic import AliasGenerator, AnyUrl, BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from src.apps.shared.enums import CompanyMemberRole, CompanyStatus, CompanyType
from src.apps.shared.schemas import BaseOut
from src.apps.users.schemas import UserCardOut


class CompanyIn(BaseModel):
    name: str = Field(max_length=120)
    tagline: str | None = Field(default=None, max_length=128)
    description: str | None = None
    logo_url: AnyUrl | None = None
    website_url: AnyUrl | None = None
    type: CompanyType

    country: str = Field(max_length=64)
    city: str = Field(max_length=64)

    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class CompanyUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    tagline: str | None = Field(default=None, max_length=128)
    description: str | None = None
    logo_url: AnyUrl | None = None
    website_url: AnyUrl | None = None
    type: CompanyType | None = None

    country: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)

    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class CompanyFilters(BaseModel):
    name: str | None = None
    type: CompanyType | None = None
    status: CompanyStatus | None = None
    country: str | None = None
    city: str | None = None
    has_open_vacancies: bool | None = None
    skill_ids: list[UUID] | None = Query(None)

    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))


class CompanyCardOut(BaseOut):
    name: str
    tagline: str | None
    logo_url: AnyUrl | None
    type: CompanyType
    status: CompanyStatus
    country: str
    city: str
    open_vacancies_count: int | None = None


class CompanyOut(CompanyCardOut):
    description: str | None
    website_url: AnyUrl | None
    contact_email: str | None
    contact_phone: str | None
    member_count: int | None = None


# ---------------------------------------------------------------------------
# Company Member
# ---------------------------------------------------------------------------
class CompanyMemberInviteIn(BaseModel):
    user_id: UUID
    role: CompanyMemberRole = CompanyMemberRole.member


class CompanyMemberRoleUpdateIn(BaseModel):
    role: CompanyMemberRole


class CompanyMemberOut(BaseOut):
    user: UserCardOut
    company_id: UUID
    role: CompanyMemberRole
