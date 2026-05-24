from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3
from pathlib import Path


@contextmanager
def sqlite_connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(database_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            yield conn
    finally:
        conn.close()
