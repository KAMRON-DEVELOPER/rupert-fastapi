from typing import TypedDict

from pydantic import BaseModel, Field


class EngagementStatus(TypedDict):
    is_quoted: bool
    is_reposted: bool
    is_liked: bool
    is_viewed: bool
    is_bookmarked: bool


class MessageRes(BaseModel):
    msg: str = Field(serialization_alias="message")
