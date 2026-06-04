from datetime import datetime, timezone
from typing import Protocol, Optional, Callable
import itertools
import httpx


class ServiceNowClient(Protocol):
    async def list(self, table: str, query: Optional[dict] = None) -> list[dict]: ...
    async def get(self, table: str, sys_id: str) -> Optional[dict]: ...
    async def create(self, table: str, payload: dict) -> dict: ...
    async def update(self, table: str, sys_id: str, payload: dict) -> dict: ...


class FakeServiceNow:
    """In-memory stand-in for the SN Table API. Used in tests and on the
    personal Mac (USE_FAKE=true) so no live instance is required."""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._tables: dict[str, dict[str, dict]] = {}
        self._ids = itertools.count(1)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now_iso(self) -> str:
        return self._clock().strftime("%Y-%m-%dT%H:%M:%SZ")

    def _table(self, table: str) -> dict[str, dict]:
        return self._tables.setdefault(table, {})

    async def list(self, table: str, query: Optional[dict] = None) -> list[dict]:
        rows = list(self._table(table).values())
        if query:
            rows = [r for r in rows if all(r.get(k) == v for k, v in query.items())]
        return rows

    async def get(self, table: str, sys_id: str) -> Optional[dict]:
        return self._table(table).get(sys_id)

    async def create(self, table: str, payload: dict) -> dict:
        sys_id = f"fake{next(self._ids):06d}"
        ts = self._now_iso()
        record = {**payload, "sys_id": sys_id, "sys_created_on": ts, "sys_updated_on": ts}
        self._table(table)[sys_id] = record
        return record

    async def update(self, table: str, sys_id: str, payload: dict) -> dict:
        record = self._table(table)[sys_id]
        record.update(payload)
        record["sys_updated_on"] = self._now_iso()
        return record


class HttpServiceNow:
    """Real SN Table API client. Same interface as FakeServiceNow."""

    def __init__(self, http: httpx.AsyncClient, token_provider: Optional[Callable[[], str]] = None) -> None:
        self._http = http
        self._token = token_provider

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self._token is not None:
            headers["Authorization"] = f"Bearer {self._token()}"
        return headers

    # Make real SN responses match the fake's shape: reference fields as plain
    # sys_id strings (not {link,value}) and raw stored values (not display
    # labels). Applied to every verb for consistency.
    _PARAMS = {"sysparm_display_value": "false", "sysparm_exclude_reference_link": "true"}

    @staticmethod
    def _encode_query(query: dict) -> str:
        return "^".join(f"{k}={v}" for k, v in query.items())

    async def list(self, table, query=None):
        params = dict(self._PARAMS)
        if query:
            params["sysparm_query"] = self._encode_query(query)
        r = await self._http.get(f"/api/now/table/{table}", params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()["result"]

    async def get(self, table, sys_id):
        r = await self._http.get(
            f"/api/now/table/{table}/{sys_id}", params=self._PARAMS, headers=self._headers()
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()["result"]

    async def create(self, table, payload):
        r = await self._http.post(
            f"/api/now/table/{table}", params=self._PARAMS, json=payload, headers=self._headers()
        )
        r.raise_for_status()
        return r.json()["result"]

    async def update(self, table, sys_id, payload):
        r = await self._http.patch(
            f"/api/now/table/{table}/{sys_id}", params=self._PARAMS, json=payload, headers=self._headers()
        )
        r.raise_for_status()
        return r.json()["result"]
