"""Global keyword search across records — deterministic substring match over the
main text fields. Pure logic over the ServiceNowClient interface."""
from app.servicenow import ServiceNowClient


async def search(sn: ServiceNowClient, scope: str, q: str, limit: int = 50) -> list[dict]:
    """Case-insensitive substring search across clients, tasks, contacts, notes,
    engagements, key dates. Returns hits: {type, sys_id, label, client, client_name}.
    `client`/`client_name` enable navigating to the owning client's dossier."""
    needle = (q or "").strip().lower()
    if not needle:
        return []
    clients = await sn.list(f"{scope}_client")
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}
    hits: list[dict] = []

    def add(type_: str, rec: dict, fields: list[str], client_id: str) -> None:
        hay = " ".join(str(rec.get(f, "")) for f in fields).lower()
        if needle in hay:
            hits.append({"type": type_, "sys_id": rec.get("sys_id"),
                         "label": rec.get(fields[0], "") or "(untitled)",
                         "client": client_id or "", "client_name": name_by_id.get(client_id, "")})

    for c in clients:
        add("client", c, ["name", "short_code", "email_domains", "email_aliases"], c.get("sys_id", ""))
    for t in await sn.list(f"{scope}_task"):
        add("task", t, ["title"], t.get("client", ""))
    for ct in await sn.list(f"{scope}_contact"):
        add("contact", ct, ["name", "role_title", "email"], ct.get("client", ""))
    for n in await sn.list(f"{scope}_note"):
        client_id = n.get("target_id", "") if n.get("target_table") == "client" else ""
        add("note", n, ["title", "body"], client_id)
    for e in await sn.list(f"{scope}_engagement"):
        add("engagement", e, ["name", "description"], e.get("client", ""))
    return hits[:limit]
