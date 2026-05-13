import pytest

from src.apps.shared.schemas.enums import Provider
from src.apps.users.models import OAuthUserModel
from src.apps.users.repositories.oauth_user import OAuthUsersRepository


@pytest.mark.asyncio
async def test_find_providers_by_user_id_returns_all(session, make_user):
    user = await make_user(email="oauth@example.com")
    session.add_all(
        [
            OAuthUserModel(provider_id="g-1", user_id=user.id, provider=Provider.google),
            OAuthUserModel(provider_id="gh-1", user_id=user.id, provider=Provider.github),
        ]
    )
    await session.commit()

    providers = await OAuthUsersRepository.find_providers_by_user_id(user.id, session)

    assert set(providers) == {Provider.google, Provider.github}
