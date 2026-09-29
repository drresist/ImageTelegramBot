"""Tests for opaque file id registry and callback_data length."""
import time
from pathlib import Path

import pytest

from file_store import CALLBACK_DATA_MAX_BYTES, FileStore


@pytest.fixture
def store(tmp_path: Path) -> FileStore:
    return FileStore(tmp_path / "file_index.json", ttl_hours=24)


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"fake-image")
    return path


class TestFileStoreRegisterResolve:
    def test_register_and_resolve(self, store: FileStore, sample_file: Path):
        file_id = store.register(sample_file, owner_id=42)
        assert len(file_id) == 12
        resolved = store.resolve(file_id, owner_id=42)
        assert resolved == sample_file

    def test_foreign_owner_denied(self, store: FileStore, sample_file: Path):
        file_id = store.register(sample_file, owner_id=42)
        assert store.resolve(file_id, owner_id=99) is None

    def test_unknown_id_returns_none(self, store: FileStore):
        assert store.resolve("deadbeefcafe", owner_id=1) is None

    def test_missing_file_returns_none(self, store: FileStore, sample_file: Path):
        file_id = store.register(sample_file, owner_id=42)
        sample_file.unlink()
        assert store.resolve(file_id, owner_id=42) is None

    def test_persists_across_instances(self, tmp_path: Path, sample_file: Path):
        index = tmp_path / "file_index.json"
        first = FileStore(index, ttl_hours=24)
        file_id = first.register(sample_file, owner_id=7)
        second = FileStore(index, ttl_hours=24)
        assert second.resolve(file_id, owner_id=7) == sample_file

    def test_expired_entry_not_resolved(self, tmp_path: Path, sample_file: Path):
        store = FileStore(tmp_path / "file_index.json", ttl_hours=0.0001)
        file_id = store.register(sample_file, owner_id=1)
        time.sleep(0.4)
        assert store.resolve(file_id, owner_id=1) is None


class TestCallbackData:
    def test_build_and_parse_roundtrip(self, store: FileStore):
        data = store.build_callback_data("exif", "abcdef012345")
        assert data == "exif:abcdef012345"
        assert FileStore.parse_callback_data(data) == ("exif", "abcdef012345")

    def test_all_options_under_64_bytes(self, store: FileStore, sample_file: Path):
        """Acceptance: callback_data always ≤64 bytes for every option."""
        file_id = store.register(sample_file, owner_id=1)
        for option in ("exif", "cropx2", "score", "geo"):
            data = store.build_callback_data(option, file_id)
            size = len(data.encode("utf-8"))
            assert size <= CALLBACK_DATA_MAX_BYTES, f"{option}: {size} bytes"
            # Must not contain path separators or the real filename
            assert "/" not in data
            assert "\\" not in data
            assert sample_file.name not in data

    def test_legacy_path_style_rejected_by_parser(self):
        legacy = "cache/photo_AgACAgIAAxk.jpg exif"
        assert FileStore.parse_callback_data(legacy) is None

    def test_parse_invalid(self):
        assert FileStore.parse_callback_data("") is None
        assert FileStore.parse_callback_data("exif") is None
        assert FileStore.parse_callback_data(":onlyid") is None
        assert FileStore.parse_callback_data("exif:") is None
