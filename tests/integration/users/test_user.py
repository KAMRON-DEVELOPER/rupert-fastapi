import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_update_delete_user_flow(client, login_client):
    user = await login_client(email="me@example.com", first_name="Me", last_name="Now")

    get_res = await client.get("/api/v1/users/")
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "me@example.com"

    patch_res = await client.patch("/api/v1/users/", json={"headline": "new headline"})
    assert patch_res.status_code == 200
    assert patch_res.json()["headline"] == "new headline"

    del_res = await client.delete("/api/v1/users/")
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_get_user_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/users/")
    assert res.status_code == 401
