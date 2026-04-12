from fastapi import APIRouter

from . import vacancy

__all__ = ["vacancy"]

vacancies_router = APIRouter()
