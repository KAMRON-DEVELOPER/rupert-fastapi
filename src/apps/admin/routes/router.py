from fastapi import APIRouter, Depends

from src.dependencies.proactive_refresh import admin_auth_dep

admin_router = APIRouter(dependencies=[Depends(admin_auth_dep)])
