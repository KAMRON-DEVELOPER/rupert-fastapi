from uuid import UUID

from src.apps.shared.schemas import ResponseSchema
from src.apps.shared.schemas.enums import Provider


class OAuthUserResponse(ResponseSchema):
    user_id: UUID
    provider: Provider
    username: str | None
    email: str | None
    picture: str | None
