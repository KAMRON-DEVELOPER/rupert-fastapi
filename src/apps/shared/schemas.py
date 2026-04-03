from typing import TypedDict


class EngagementStatus(TypedDict):
    is_quoted: bool
    is_reposted: bool
    is_liked: bool
    is_viewed: bool
    is_bookmarked: bool
