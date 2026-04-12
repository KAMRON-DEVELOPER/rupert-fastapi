from uuid import UUID

from pydantic import AnyUrl, BaseModel, EmailStr, Field

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


class CompanyCardOut(BaseOut):
    name: str
    tagline: str | None
    logo_url: AnyUrl | None
    type: CompanyType
    country: str
    city: str
    status: CompanyStatus


class CompanyOut(CompanyCardOut):
    description: str | None
    website_url: AnyUrl | None
    contact_email: str | None
    contact_phone: str | None

    member_count: int | None = None
    open_vacancy_count: int | None = None


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
