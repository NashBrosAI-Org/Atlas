import pytest

from app import tagging
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


async def test_get_or_create_tag_is_idempotent_by_name(sn):
    first = await tagging.get_or_create_tag(sn, SCOPE, "VIP")
    again = await tagging.get_or_create_tag(sn, SCOPE, "vip")  # case-insensitive match

    assert first["name"] == "VIP"
    assert again["sys_id"] == first["sys_id"]
    assert len(await sn.list(f"{SCOPE}_tag")) == 1


async def test_attach_tag_creates_link_once(sn):
    link = await tagging.attach_tag(sn, SCOPE, "VIP", "client", "c1")

    assert link["target_table"] == "client"
    assert link["target_id"] == "c1"
    tag_id = link["tag"]

    # Re-attaching the same tag to the same record is idempotent — no duplicate link.
    again = await tagging.attach_tag(sn, SCOPE, "vip", "client", "c1")
    assert again["sys_id"] == link["sys_id"]
    assert len(await sn.list(f"{SCOPE}_tag_m2m")) == 1

    # Same tag on a different record is a new link.
    other = await tagging.attach_tag(sn, SCOPE, "VIP", "client", "c2")
    assert other["tag"] == tag_id
    assert len(await sn.list(f"{SCOPE}_tag_m2m")) == 2


async def test_tags_for_resolves_names_sorted(sn):
    await tagging.attach_tag(sn, SCOPE, "VIP", "client", "c1")
    await tagging.attach_tag(sn, SCOPE, "renewal", "client", "c1")
    await tagging.attach_tag(sn, SCOPE, "elsewhere", "client", "c2")

    tags = await tagging.tags_for(sn, SCOPE, "client", "c1")

    assert [t["name"] for t in tags] == ["renewal", "VIP"]  # case-insensitive sort
    assert all("sys_id" in t and "link_id" in t for t in tags)
    assert await tagging.tags_for(sn, SCOPE, "client", "no-tags") == []


async def test_detach_tag_removes_only_that_link(sn):
    await tagging.attach_tag(sn, SCOPE, "VIP", "client", "c1")
    await tagging.attach_tag(sn, SCOPE, "renewal", "client", "c1")
    vip = next(t for t in await tagging.tags_for(sn, SCOPE, "client", "c1") if t["name"] == "VIP")

    removed = await tagging.detach_tag(sn, SCOPE, vip["sys_id"], "client", "c1")

    assert removed is True
    remaining = await tagging.tags_for(sn, SCOPE, "client", "c1")
    assert [t["name"] for t in remaining] == ["renewal"]
    # The tag itself stays in the vocabulary (only the link is removed).
    assert len(await sn.list(f"{SCOPE}_tag")) == 2
    # Detaching a tag that isn't on the record is a no-op.
    assert await tagging.detach_tag(sn, SCOPE, vip["sys_id"], "client", "c1") is False
