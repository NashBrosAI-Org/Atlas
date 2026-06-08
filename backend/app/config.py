import os

from pydantic_settings import BaseSettings, SettingsConfigDict

import app.user_config as user_config

# Which dotenv file to load. Defaults to `.env` in production; tests set
# ATLAS_ENV_FILE="" (→ None) so they never pick up the dev machine's live
# backend/.env (which points at the real instance) — keeps tests deterministic.
_ENV_FILE = os.environ.get("ATLAS_ENV_FILE", ".env") or None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    use_fake: bool = True
    sn_instance_url: str = "https://example.service-now.com"
    sn_scope: str = "x_atlas_sn"  # matches the deployed scoped app (servicenow/now.config.json)
    sn_auth: str = "basic"  # "basic" (D11) or "oauth"
    sn_oauth_client_id: str = ""
    sn_oauth_client_secret: str = ""
    sn_oauth_username: str = ""
    sn_oauth_password: str = ""
    m365_use_fake: bool = True   # personal Mac builds against FakeGraph (hard rule #1)
    # Which mail the live HttpGraph (Phase 4) ingests — keeps the retained corporate
    # scope narrow and user-controlled (risks R1/D2). "inbox" | "inbox_sent" | "flagged_only".
    m365_mail_filter: str = "inbox"
    cooling_days: int = 14
    stale_days: int = 30
    backup_max_age_days: int = 7  # a backup older than this is "stale" (Plan 3d)
    ai_enabled: bool = False                                  # gates the AI UI; additive (rule #6)
    ai_use_fake: bool = True                                  # personal Mac builds against FakeAI
    anthropic_model: str = "claude-haiku-4-5-20251001"


def get_settings() -> Settings:
    """Env/.env defaults, overlaid with the user's saved config.json and the
    Keychain password (so in-app Settings take effect without code changes)."""
    overlay = user_config.load_overlay()
    base = Settings()
    merged = base.model_dump()
    merged.update({k: v for k, v in overlay.items() if k in merged})
    settings = Settings(**merged)
    pw = user_config.get_password()
    if pw is not None:
        settings.sn_oauth_password = pw
    return settings
