"""Extract structured contact fields from an email signature — AI-primary with a
deterministic regex fallback so it still works when the model returns junk (or the
demo FakeAI). Pure logic over AIClient. Additive; only /api/ai/* calls it."""
import json
import re

from app.ai import AIClient

_FIELDS = ("name", "role_title", "email", "phone")
_SYSTEM = ('Extract the sender\'s details from this email signature. Respond with ONLY a JSON object '
           'with keys "name", "role_title", "email", "phone" (use "" for anything missing). No prose.')
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def _parse_json(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _regex_extract(signature: str) -> dict:
    sig = signature or ""
    out: dict = {}
    m = _EMAIL_RE.search(sig)
    if m:
        out["email"] = m.group(0)
    p = _PHONE_RE.search(sig)
    if p:
        out["phone"] = p.group(0).strip()
    for line in sig.splitlines():           # signatures usually lead with the name
        if line.strip():
            out["name"] = line.strip()
            break
    return out


async def extract_contact_fields(ai: AIClient, signature: str) -> dict:
    """Return {name, role_title, email, phone}. Prefer the AI's JSON; fill any gaps
    from a regex pass. Always returns all four keys (empty string when unknown)."""
    raw = await ai.complete(system=_SYSTEM, prompt=signature, max_tokens=300)
    ai_data = _parse_json(raw)
    fallback = _regex_extract(signature)
    return {k: (str(ai_data.get(k) or "").strip() or fallback.get(k, "")) for k in _FIELDS}
