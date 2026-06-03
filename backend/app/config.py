from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_fake: bool = True
    sn_instance_url: str = "https://example.service-now.com"
    sn_scope: str = "x_atlas_sn"
    # Live auth. Basic is the default — nnash (Zurich) walls the inbound-OAuth
    # endpoints the token flow needs, so we authenticate as a local user (D11).
    sn_auth_type: Literal["basic", "oauth"] = "basic"
    sn_username: str = ""
    sn_password: str = ""
    # Legacy OAuth password grant (kept for non-walled instances).
    sn_oauth_client_id: str = ""
    sn_oauth_client_secret: str = ""
    sn_oauth_username: str = ""
    sn_oauth_password: str = ""


def get_settings() -> Settings:
    return Settings()
