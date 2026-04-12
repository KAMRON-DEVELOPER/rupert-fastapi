from fastapi import APIRouter

from . import auth

__all__ = ["auth"]

users_router = APIRouter()
