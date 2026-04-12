from fastapi import APIRouter

from . import company

__all__ = ["company"]

companies_router = APIRouter()
