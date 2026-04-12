from dead_simple_oauth_fastapi import GitHubOAuthClient, GoogleOAuthClient

from src.core.settings import get_settings

settings = get_settings()

google = GoogleOAuthClient(
    client_id=settings.google_oauth.client_id,
    client_secret=settings.google_oauth.client_secret,
    redirect_uri=settings.google_oauth.redirect_url,
)

github = GitHubOAuthClient(
    client_id=settings.github_oauth.client_id,
    client_secret=settings.github_oauth.client_secret,
    redirect_uri=settings.github_oauth.redirect_url,
)
