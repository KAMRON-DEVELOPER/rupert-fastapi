from .base import ResponseSchema


class MessageResponse(ResponseSchema):
    message: str
