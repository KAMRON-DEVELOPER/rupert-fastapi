from uuid import UUID
from fastapi import APIRouter

upload_router = APIRouter()


@upload_router.post("/")
async def upload():
    pass


@upload_router.delete("/{attachment_id}")
async def delete(attachment_id: UUID):
    pass
