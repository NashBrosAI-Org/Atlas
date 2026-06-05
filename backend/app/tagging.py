"""Tagging: a cross-cutting label vocabulary (`tag`) plus a polymorphic
many-to-many join (`tag_m2m`) that pins a tag to any record. Pure logic over the
ServiceNowClient interface, mirroring Note's `target_table`+`target_id` pinning
(Plan 3b). Unit-tested against FakeServiceNow."""
from typing import Optional

from app.servicenow import ServiceNowClient


def _t(scope: str, suffix: str) -> str:
    return f"{scope}_{suffix}"


async def get_or_create_tag(sn: ServiceNowClient, scope: str, name: str) -> dict:
    """Find a tag by case-insensitive name, creating it if absent (names are unique)."""
    name = name.strip()
    wanted = name.casefold()
    for tag in await sn.list(_t(scope, "tag")):
        if tag.get("name", "").strip().casefold() == wanted:
            return tag
    return await sn.create(_t(scope, "tag"), {"name": name})


async def _find_link(sn: ServiceNowClient, scope: str, tag_id: str,
                     target_table: str, target_id: str) -> Optional[dict]:
    links = await sn.list(_t(scope, "tag_m2m"),
                          query={"tag": tag_id, "target_table": target_table, "target_id": target_id})
    return links[0] if links else None


async def attach_tag(sn: ServiceNowClient, scope: str, name: str,
                     target_table: str, target_id: str) -> dict:
    """Tag a record. Get-or-create the tag, then create the m2m link if the record
    isn't already tagged with it (idempotent)."""
    tag = await get_or_create_tag(sn, scope, name)
    existing = await _find_link(sn, scope, tag["sys_id"], target_table, target_id)
    if existing is not None:
        return existing
    return await sn.create(_t(scope, "tag_m2m"),
                           {"tag": tag["sys_id"], "target_table": target_table, "target_id": target_id})


async def tags_for(sn: ServiceNowClient, scope: str,
                   target_table: str, target_id: str) -> list[dict]:
    """The tags pinned to a record, name-resolved and sorted. Each entry carries
    `link_id` (the m2m sys_id) so the caller can detach it."""
    links = await sn.list(_t(scope, "tag_m2m"),
                          query={"target_table": target_table, "target_id": target_id})
    if not links:
        return []
    names = {t["sys_id"]: t.get("name", "") for t in await sn.list(_t(scope, "tag"))}
    tags = [{"sys_id": ln["tag"], "name": names.get(ln["tag"], ""), "link_id": ln["sys_id"]}
            for ln in links]
    return sorted(tags, key=lambda t: t["name"].casefold())


async def detach_tag(sn: ServiceNowClient, scope: str, tag_id: str,
                     target_table: str, target_id: str) -> bool:
    """Remove a tag from a record (delete the m2m link). The tag stays in the
    vocabulary. Returns False if the record wasn't tagged with it."""
    link = await _find_link(sn, scope, tag_id, target_table, target_id)
    if link is None:
        return False
    return await sn.delete(_t(scope, "tag_m2m"), link["sys_id"])
