from __future__ import annotations

import re
import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parent
SCHEMA_SQL = "\n".join(
    [
        (MIGRATIONS_DIR / "001_init.sql").read_text(encoding="utf-8"),
        (MIGRATIONS_DIR / "003_appearance_profiles.sql").read_text(encoding="utf-8"),
    ]
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_identifier(value: str, *, kind: str = "identifier") -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid SQLite {kind}: {value!r}")
    return value


def ensure_column(conn: sqlite3.Connection, *, table: str, column: str, definition: str) -> None:
    table = validate_identifier(table, kind="table")
    column = validate_identifier(column, kind="column")
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column in columns:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
