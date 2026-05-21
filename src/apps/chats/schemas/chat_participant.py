from datetime import datetime
from uuid import UUID

from pydantic import computed_field

from src.apps.shared.schemas import RequestSchema, ResponseSchema


class ChatSettingsRequest(RequestSchema):
    is_pinned: bool | None = None
    is_muted: bool | None = None
    is_archived: bool | None = None


class ChatListUserResponse(ResponseSchema):
    id: UUID
    first_name: str
    last_name: str | None = None
    avatar_url: str | None = None

    @computed_field
    @property
    def name(self) -> str:
        return " ".join(
            part for part in [self.first_name, self.last_name] if part
        )


class LastSeenAtRequest(RequestSchema):
    last_seen_at: datetime
