"""Opaque file id registry for Telegram callback_data."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Optional, Tuple

# Telegram InlineKeyboardButton.callback_data hard limit
CALLBACK_DATA_MAX_BYTES = 64


@dataclass
class FileEntry:
    path: str
    owner_id: int
    created_at: float


class FileStore:
    """Maps short opaque ids to cached file paths with ownership and TTL."""

    def __init__(self, store_path: Path, ttl_hours: float = 24.0):
        self.store_path = Path(store_path)
        self.ttl_seconds = ttl_hours * 3600
        self._lock = Lock()
        self._entries: dict[str, FileEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        try:
            raw = json.loads(self.store_path.read_text(encoding="utf-8"))
            entries: dict[str, FileEntry] = {}
            for file_id, payload in raw.items():
                entries[file_id] = FileEntry(
                    path=str(payload["path"]),
                    owner_id=int(payload["owner_id"]),
                    created_at=float(payload["created_at"]),
                )
            self._entries = entries
        except (json.JSONDecodeError, TypeError, KeyError, ValueError, OSError):
            self._entries = {}
        self._purge_expired(persist=False)

    def _persist(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {file_id: asdict(entry) for file_id, entry in self._entries.items()}
        tmp = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(self.store_path)

    def _purge_expired(self, persist: bool = True) -> None:
        now = time.time()
        expired = [
            file_id
            for file_id, entry in self._entries.items()
            if now - entry.created_at > self.ttl_seconds
        ]
        for file_id in expired:
            del self._entries[file_id]
        if persist and expired:
            self._persist()

    def register(self, path: Path, owner_id: int) -> str:
        """Store path under a new opaque id owned by owner_id. Returns the id."""
        with self._lock:
            self._purge_expired(persist=False)
            file_id = uuid.uuid4().hex[:12]
            while file_id in self._entries:
                file_id = uuid.uuid4().hex[:12]
            self._entries[file_id] = FileEntry(
                path=str(path),
                owner_id=int(owner_id),
                created_at=time.time(),
            )
            self._persist()
            return file_id

    def resolve(self, file_id: str, owner_id: int) -> Optional[Path]:
        """Return path only if id exists, not expired, and owned by owner_id."""
        with self._lock:
            self._purge_expired(persist=False)
            entry = self._entries.get(file_id)
            if entry is None:
                return None
            if entry.owner_id != int(owner_id):
                return None
            path = Path(entry.path)
            if not path.is_file():
                return None
            return path

    @staticmethod
    def build_callback_data(option: str, file_id: str) -> str:
        data = f"{option}:{file_id}"
        size = len(data.encode("utf-8"))
        if size > CALLBACK_DATA_MAX_BYTES:
            raise ValueError(
                f"callback_data exceeds {CALLBACK_DATA_MAX_BYTES} bytes: {size}"
            )
        return data

    @staticmethod
    def parse_callback_data(data: str) -> Optional[Tuple[str, str]]:
        if ":" not in data:
            return None
        option, file_id = data.split(":", 1)
        if not option or not file_id:
            return None
        return option, file_id
