from uuid import UUID

from src.apps.shared.schemas import BaseModelResponse, RequestSchema
from src.apps.shared.schemas.enums import (
    FollowPolicy,
    FollowStatus,
    JobSearchStatus,
    Specialization,
)


class FollowUserResponse(BaseModelResponse):
    first_name: str
    last_name: str | None
    headline: str | None
    avatar_url: str | None
    specialization: Specialization | None
    follow_policy: FollowPolicy
    job_search_status: JobSearchStatus
    followers_count: int
    followings_count: int


class FollowResponse(BaseModelResponse):
    follower_id: UUID
    following_id: UUID
    status: FollowStatus
    follower: FollowUserResponse | None = None
    following: FollowUserResponse | None = None


class FollowUpdateRequest(RequestSchema):
    status: FollowStatus
