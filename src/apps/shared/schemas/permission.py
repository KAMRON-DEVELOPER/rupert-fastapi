from .base import ResponseSchema


class PermissionSchema(ResponseSchema):
    is_owner: bool = False
