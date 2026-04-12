from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, JsonConfigSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict
from types_aiobotocore_s3.literals import BucketLocationConstraintType


class DatabaseConfig(BaseModel):
    url: str = "postgresql+asyncpg://postgres:password@localhost:5432/rupert_db"
    pool_size: int = 10


class RedisSsl(BaseModel):
    ssl: bool = False
    ssl_ca_certs: str = ""
    ssl_certfile: str = ""
    ssl_keyfile: str = ""
    ssl_cert_reqs: str = ""
    ssl_check_hostname: bool = True


class RedisParams(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    username: str | None = None
    password: str | None = None


class RedisConfig(BaseModel):
    url: str | None = "redis://localhost:6379/0?decode_responses=True&protocol=3"
    params: RedisParams | None = RedisParams()
    ssl: RedisSsl | None = None


class GoogleOauthConfig(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    redirect_url: str = ""


class GithubOauthConfig(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    redirect_url: str = ""


class MailtrapTemplateConfig(BaseModel):
    from_email: str = ""
    from_name: str = ""
    template_uuid: str = ""


class MailtrapConfig(BaseModel):
    api_key: str = ""
    verification: MailtrapTemplateConfig = MailtrapTemplateConfig()
    password_setup: MailtrapTemplateConfig = MailtrapTemplateConfig()
    billing: MailtrapTemplateConfig = MailtrapTemplateConfig()
    support: MailtrapTemplateConfig = MailtrapTemplateConfig()
    feedback_confirmation: MailtrapTemplateConfig = MailtrapTemplateConfig()


class S3Config(BaseModel):
    access_key_id: str = ""
    secret_key: str = ""
    endpoint: str = ""
    region: BucketLocationConstraintType = "me-central-1"
    bucket_name: str = ""


class JwtConfig(BaseModel):
    secret_key: str = ""
    algorithm: str = "HS256"
    domain: str | None = None
    access_token_expire_in_minutes: int = 60
    refresh_token_expire_in_days: int = 90
    email_verification_token_expire_in_hours: int = 24
    password_setup_token_expire_in_minutes: int = 60
    access_token_renewal_threshold_minutes: int = 5
    refresh_token_renewal_threshold_days: int = 5


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).parent.parent.parent.resolve()

    debug: bool = True
    frontend_endpoint: str = "http://localhost:5173"
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    google_oauth: GoogleOauthConfig = GoogleOauthConfig()
    github_oauth: GithubOauthConfig = GithubOauthConfig()
    mailtrap: MailtrapConfig = MailtrapConfig()
    s3: S3Config = S3Config()
    jwt: JwtConfig = JwtConfig()

    model_config = SettingsConfigDict(json_file="config.json", extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings():
    return Settings()
