"""Persistent attempt limits. No prompts, replies, keys or audio in this ledger."""
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import time

from .providers import ProviderError


class Usage:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.clock = clock
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        os.chmod(self.path, 0o600)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS attempts (at REAL NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=3)

    def _day_start(self, now):
        return datetime.fromtimestamp(now, timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    def count_today(self):
        now = self.clock()
        with self._connect() as db:
            return db.execute("SELECT COUNT(*) FROM attempts WHERE at>=?", (self._day_start(now),)).fetchone()[0]

    def reserve(self, settings):
        now = self.clock()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            today = db.execute("SELECT COUNT(*) FROM attempts WHERE at>=?", (self._day_start(now),)).fetchone()[0]
            recent = db.execute("SELECT COUNT(*) FROM attempts WHERE at>?", (now - 60,)).fetchone()[0]
            if today >= settings.daily_requests:
                raise ProviderError("daily_request_limit")
            if recent >= settings.requests_per_minute:
                raise ProviderError("minute_request_limit")
            db.execute("INSERT INTO attempts VALUES (?)", (now,))
            db.execute("DELETE FROM attempts WHERE at<?", (now - 32 * 86400,))
