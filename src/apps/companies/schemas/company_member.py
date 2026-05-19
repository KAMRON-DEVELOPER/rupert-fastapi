from uuid import UUID

from src.apps.shared.schemas import BaseModelResponse, RequestSchema
from src.apps.shared.schemas.enums import CompanyMemberRole
from src.apps.users.schemas.user import UserSummaryResponse


class CompanyMemberInviteRequest(RequestSchema):
    user_id: UUID
    role: CompanyMemberRole = CompanyMemberRole.member


class CompanyMemberRoleUpdateRequest(RequestSchema):
    role: CompanyMemberRole


class CompanyMemberResponse(BaseModelResponse):
    user: UserSummaryResponse
    company_id: UUID
    role: CompanyMemberRole
