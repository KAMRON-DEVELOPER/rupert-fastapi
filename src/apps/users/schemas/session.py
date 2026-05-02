from datetime import datetime
from uuid import UUID

from src.apps.shared.schemas import ResponseSchema


class SessionResponse(ResponseSchema):
    user_id: UUID
    user_agent: str | None
    ip_addr: str | None
    device_name: str | None
    is_active: bool
    last_activity_at: datetime
