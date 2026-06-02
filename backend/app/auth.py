import time
import httpx
import keyring
from app.config import Settings

_KEYRING_SERVICE = "atlas-sn"


class TokenManager:
    """Acquires and refreshes a ServiceNow OAuth token. Caches the refresh
    token in the macOS Keychain so the client secret/password aren't needed
    after first login."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def _token_url(self) -> str:
        return f"{self._s.sn_instance_url}/oauth_token.do"

    def get_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token
        refresh = keyring.get_password(_KEYRING_SERVICE, "refresh_token")
        data = {
            "client_id": self._s.sn_oauth_client_id,
            "client_secret": self._s.sn_oauth_client_secret,
        }
        if refresh:
            data |= {"grant_type": "refresh_token", "refresh_token": refresh}
        else:
            data |= {
                "grant_type": "password",
                "username": self._s.sn_oauth_username,
                "password": self._s.sn_oauth_password,
            }
        resp = httpx.post(self._token_url(), data=data, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        self._expires_at = time.time() + int(body.get("expires_in", 1800))
        if body.get("refresh_token"):
            keyring.set_password(_KEYRING_SERVICE, "refresh_token", body["refresh_token"])
        return self._access_token
