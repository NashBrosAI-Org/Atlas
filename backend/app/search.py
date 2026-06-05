"""Global keyword search across records — deterministic, tiered-ranked substring
match over the main text fields. Pure logic over the ServiceNowClient interface."""
from typing import Optional

from app.servicenow import ServiceNowClient

# Score tiers (higher = better match).
TITLE_EXACT = 1000
TITLE_PREFIX = 900
TITLE_CONTAINS = 800
SECONDARY = 500
BODY = 200

# Per type: (table suffix, label field, secondary fields, body fields).
# The label field is the display label; "" means the type has no label (transcript).
_SPECS: dict[str, tuple[str, str, list[str], list[str]]] = {
    "client": ("client", "name", ["short_code", "email_domains", "email_aliases"], ["notes"]),
    "task": ("task", "title", ["theme"], []),
    "contact": ("contact", "name", ["role_title", "email", "phone"], ["personal_notes"]),
    "note": ("note", "title", [], ["body"]),
    "engagement": ("engagement", "name", [], ["description"]),
    "meeting": ("meeting", "title", ["attendees"], ["summary"]),
    "theme": ("theme", "name", [], ["description"]),
    "key_date": ("key_date", "title", ["date"], []),
    "link": ("link", "title", ["url"], []),
    "transcript": ("transcript", "", [], ["full_text"]),
}

# Display/scan order (registry order).
TYPE_ORDER = list(_SPECS.keys())
# Default scope excludes transcripts (long, noisy); opt in via `types`.
DEFAULT_TYPES = [t for t in TYPE_ORDER if t != "transcript"]

_TRANSCRIPT_LABEL = "Transcript"
_SNIPPET_RADIUS = 30


def _snippet(text: str, start: int, end: int) -> str:
    """A short context window around a body match, with the match delimited by
    `>>` `<<` so the frontend can highlight it."""
    lo = max(0, start - _SNIPPET_RADIUS)
    hi = min(len(text), end + _SNIPPET_RADIUS)
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(text) else ""
    return f"{prefix}{text[lo:start]}>>{text[start:end]}<<{text[end:hi]}{suffix}"


def _score(label: str, secondary: list[str], body: list[str],
           needle: str) -> tuple[int, Optional[str]]:
    """Best tier for one record. Title tiers beat secondary beat body. Body hits
    carry a snippet; title/secondary hits don't."""
    ll = label.lower()
    if ll and ll == needle:
        return TITLE_EXACT, None
    if ll and ll.startswith(needle):
        return TITLE_PREFIX, None
    if ll and needle in ll:
        return TITLE_CONTAINS, None
    for value in secondary:
        if needle in value.lower():
            return SECONDARY, None
    for value in body:
        idx = value.lower().find(needle)
        if idx >= 0:
            return BODY, _snippet(value, idx, idx + len(needle))
    return 0, None


def _client_id(type_: str, rec: dict) -> str:
    """The owning client's sys_id for navigation (empty when none)."""
    if type_ == "client":
        return rec.get("sys_id", "") or ""
    if type_ == "note":
        return rec.get("target_id", "") if rec.get("target_table") == "client" else ""
    return rec.get("client", "") or ""


async def search(sn: ServiceNowClient, scope: str, q: str, limit: int = 50,
                 types: Optional[list[str]] = None) -> list[dict]:
    """Case-insensitive, tiered-ranked substring search across record types.

    Returns hits ``{type, sys_id, label, client, client_name, score, snippet}``
    sorted by (type order, score desc, shorter label). ``types`` selects which
    record types to search; ``None`` means all types except transcripts.
    ``limit`` is applied **per type** so a broad query matching many types can
    never silently drop a whole type behind a global cutoff.
    ``client``/``client_name`` enable navigating to the owning client's dossier.
    """
    needle = (q or "").strip().lower()
    if not needle:
        return []

    selected = set(types) if types is not None else set(DEFAULT_TYPES)
    wanted = [t for t in TYPE_ORDER if t in selected]

    clients = await sn.list(f"{scope}_client")
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}

    result: list[dict] = []
    for type_ in wanted:
        suffix, label_field, secondary_fields, body_fields = _SPECS[type_]
        rows = clients if type_ == "client" else await sn.list(f"{scope}_{suffix}")
        group: list[dict] = []
        for rec in rows:
            label = str(rec.get(label_field, "") or "") if label_field else _TRANSCRIPT_LABEL
            secondary = [str(rec.get(f, "") or "") for f in secondary_fields]
            body = [str(rec.get(f, "") or "") for f in body_fields]
            score, snippet = _score(label, secondary, body, needle)
            if score == 0:
                continue
            cid = _client_id(type_, rec)
            group.append({
                "type": type_,
                "sys_id": rec.get("sys_id"),
                "label": label or "(untitled)",
                "client": cid,
                "client_name": name_by_id.get(cid, ""),
                "score": score,
                "snippet": snippet,
            })
        # Rank within the type, then cap this type — so types later in the order
        # are never dropped by a single global cutoff.
        group.sort(key=lambda h: (-h["score"], len(h["label"]), h["label"].lower()))
        result.extend(group[:limit])
    return result
