from typing import Annotated
from uuid import UUID

from fastapi import Query, status

from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.companies.schemas.company import (
    CompanyCreateRequest,
    CompanyDetail,
    CompanySummary,
    CompanyUpdateRequest,
    companyListDep,
)
from src.apps.companies.schemas.company_member import (
    CompanyMemberInviteRequest,
    CompanyMemberResponse,
    CompanyMemberRoleUpdateRequest,
)
from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep, authProbeDep

from .router import companies_router


@companies_router.post(
    "/", response_model=CompanyDetail, status_code=status.HTTP_201_CREATED
)
async def create_company(
    auth: authDep, session: sessionDep, schm: CompanyCreateRequest
):
    user_id, _, _ = auth
    record = await CompaniesRepository.create(
        session, user_id, schm.model_dump(mode="json")
    )
    await session.commit()
    return CompanyDetail.model_validate(record)


@companies_router.patch("/{company_id}", response_model=CompanyDetail)
async def update_company(
    auth: authDep,
    session: sessionDep,
    company_id: UUID,
    schm: CompanyUpdateRequest,
):
    user_id, _, _ = auth
    record = await CompaniesRepository.update(
        session,
        user_id,
        company_id,
        schm.model_dump(mode="json", exclude_unset=True),
    )
    await session.commit()
    return CompanyDetail.model_validate(record)


@companies_router.delete(
    "/{company_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_company(auth: authDep, session: sessionDep, company_id: UUID):
    user_id, _, _ = auth
    await CompaniesRepository.delete(session, user_id, company_id)
    await session.commit()
    return MessageResponse(message="Company deleted successfully")


@companies_router.get("/", response_model=PaginatedResponse[CompanySummary])
async def list_companies(
    auth: authProbeDep,
    pagination: paginationDep,
    filters: companyListDep,
    session: sessionDep,
    own: Annotated[bool, Query()] = False,
):
    user_id = auth[0] if auth and own else None
    return await CompaniesRepository.get_many(
        session=session, pagination=pagination, filters=filters, user_id=user_id
    )


@companies_router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(company_id: UUID, session: sessionDep):
    record = await CompaniesRepository.get(session, company_id)
    return CompanyDetail.model_validate(record)


@companies_router.post(
    "/{company_id}/members",
    response_model=CompanyMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_company_member(
    auth: authDep,
    session: sessionDep,
    company_id: UUID,
    schm: CompanyMemberInviteRequest,
):
    user_id, _, _ = auth
    record = await CompaniesRepository.add_member(
        session, user_id, company_id, schm.model_dump()
    )
    await session.commit()
    return CompanyMemberResponse.model_validate(record)


@companies_router.patch(
    "/{company_id}/members/{member_id}", response_model=CompanyMemberResponse
)
async def update_company_member(
    auth: authDep,
    session: sessionDep,
    company_id: UUID,
    member_id: UUID,
    schm: CompanyMemberRoleUpdateRequest,
):
    user_id, _, _ = auth
    record = await CompaniesRepository.update_member(
        session, user_id, company_id, member_id, schm.model_dump()
    )
    await session.commit()
    return CompanyMemberResponse.model_validate(record)


@companies_router.delete(
    "/{company_id}/members/{member_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_company_member(
    auth: authDep, session: sessionDep, company_id: UUID, member_id: UUID
):
    user_id, _, _ = auth
    await CompaniesRepository.delete_member(
        session, user_id, company_id, member_id
    )
    await session.commit()
    return MessageResponse(message="Company member deleted successfully")
