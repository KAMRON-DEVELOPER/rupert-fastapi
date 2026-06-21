from typing import Annotated

from fastapi import Depends
from pydantic import AnyUrl, EmailStr, Field

from src.apps.companies.schemas.company_member import CompanyMemberResponse
from src.apps.shared.schemas import BaseLocationModelResponse, LocationRequest
from src.apps.shared.schemas.enums import CompanyStatus, CompanyType
from src.apps.shared.schemas.location import NullableLocationRequest


class CompanyCreateRequest(LocationRequest):
    name: str = Field(max_length=120)
    tagline: str | None = Field(default=None, max_length=128)
    description: str | None = None
    logo_url: AnyUrl | None = None
    website_url: AnyUrl | None = None
    type: CompanyType

    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class CompanyUpdateRequest(NullableLocationRequest):
    name: str | None = Field(default=None, max_length=128)
    tagline: str | None = Field(default=None, max_length=128)
    description: str | None = None
    logo_url: AnyUrl | None = None
    website_url: AnyUrl | None = None
    type: CompanyType | None = None

    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class CompanyListParams(NullableLocationRequest):
    name: str | None = None
    type: CompanyType | None = None
    status: CompanyStatus | None = None
    has_open_vacancies: bool | None = None


companyListDep = Annotated[CompanyListParams, Depends()]


class CompanySummary(BaseLocationModelResponse):
    name: str
    tagline: str | None
    logo_url: AnyUrl | None
    type: CompanyType
    status: CompanyStatus
    open_vacancies_count: int | None = None


class CompanyDetail(CompanySummary):
    description: str | None
    website_url: AnyUrl | None
    contact_email: str | None
    contact_phone: str | None
    member_count: int | None = None
    members: list[CompanyMemberResponse] = Field(default_factory=list)
