import json
from datetime import datetime, timezone

import pytest

from app import backup
from app.servicenow import FakeServiceNow


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    return tmp_path


async def test_build_export_aggregates_all_tables_with_counts(sn):
    await sn.create("x_atlas_sn_client", {"name": "Acme"})
    await sn.create("x_atlas_sn_client", {"name": "Globex"})
    await sn.create("x_atlas_sn_task", {"title": "Call back"})

    export = await backup.build_export(sn, "x_atlas_sn", now=datetime(2026, 6, 4, tzinfo=timezone.utc))

    # Every modeled table is present, even when empty, so a backup is a full snapshot.
    assert set(export["tables"]) == set(backup.TABLES)
    assert len(export["tables"]["client"]) == 2
    assert export["counts"]["client"] == 2
    assert export["counts"]["task"] == 1
    assert export["counts"]["note"] == 0
    assert export["scope"] == "x_atlas_sn"
    assert export["created_at"] == "2026-06-04T00:00:00Z"


async def test_write_export_writes_timestamped_json_to_backups_dir(sn, data_dir):
    await sn.create("x_atlas_sn_client", {"name": "Acme"})

    path = await backup.write_export(sn, "x_atlas_sn",
                                     now=datetime(2026, 6, 4, 9, 30, 15, tzinfo=timezone.utc))

    assert path.parent == data_dir / "backups"
    assert path.name == "atlas-backup-20260604-093015.json"
    written = json.loads(path.read_text())
    assert written["counts"]["client"] == 1
    assert written["tables"]["client"][0]["name"] == "Acme"


def test_latest_backup_time_none_when_no_backups(data_dir):
    assert backup.latest_backup_time() is None


async def test_latest_backup_time_returns_most_recent(sn, data_dir):
    await backup.write_export(sn, "x_atlas_sn", now=datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc))
    await backup.write_export(sn, "x_atlas_sn", now=datetime(2026, 6, 3, 8, 0, 0, tzinfo=timezone.utc))

    assert backup.latest_backup_time() == datetime(2026, 6, 3, 8, 0, 0, tzinfo=timezone.utc)


async def test_is_backup_stale(sn, data_dir):
    now = datetime(2026, 6, 10, tzinfo=timezone.utc)
    # No backups yet → stale.
    assert backup.is_backup_stale(max_age_days=7, now=now) is True

    await backup.write_export(sn, "x_atlas_sn", now=datetime(2026, 6, 8, tzinfo=timezone.utc))
    assert backup.is_backup_stale(max_age_days=7, now=now) is False  # 2 days old

    assert backup.is_backup_stale(max_age_days=1, now=now) is True  # older than 1 day


async def test_autobackup_if_stale_writes_only_when_due(sn, data_dir):
    await sn.create("x_atlas_sn_client", {"name": "Acme"})

    # First launch: no backup yet → writes one.
    first = await backup.autobackup_if_stale(sn, "x_atlas_sn", max_age_days=7,
                                             now=datetime(2026, 6, 4, tzinfo=timezone.utc))
    assert first is not None and first.is_file()

    # Same week: still fresh → no new backup.
    again = await backup.autobackup_if_stale(sn, "x_atlas_sn", max_age_days=7,
                                             now=datetime(2026, 6, 6, tzinfo=timezone.utc))
    assert again is None

    # A week later: stale → writes again.
    later = await backup.autobackup_if_stale(sn, "x_atlas_sn", max_age_days=7,
                                             now=datetime(2026, 6, 20, tzinfo=timezone.utc))
    assert later is not None and later.is_file()
