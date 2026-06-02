from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_fake: bool = True
    sn_instance_url: str = "https://example.service-now.com"
    sn_scope: str = "x_vendor_atlas"
    sn_oauth_client_id: str = ""
    sn_oauth_client_secret: str = ""
    sn_oauth_username: str = ""
    sn_oauth_password: str = ""


def get_settings() -> Settings:
    return Settings()
