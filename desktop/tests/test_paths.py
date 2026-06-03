from pathlib import Path

from desktop.paths import user_data_dir, config_file


def test_user_data_dir_default(monkeypatch):
    monkeypatch.delenv("ATLAS_DATA_DIR", raising=False)
    p = user_data_dir()
    assert p == Path.home() / "Library" / "Application Support" / "Atlas"


def test_user_data_dir_honors_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert user_data_dir() == tmp_path


def test_config_file_under_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert config_file() == tmp_path / "config.json"
