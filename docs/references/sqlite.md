# SQLite Reference

## Role in CareSight

SQLite is the local event memory and source of truth.

## Why it fits

- local file database
- no separate server
- easy to inspect and ship
- supports JSON functions
- supports full-text search via FTS5

## CareSight tables

- people
- subjects
- cameras
- zones
- routines
- events
- event_observations
- journal_entries
- alerts
- audit_log

## Sources

- [SQLite Main Docs](https://sqlite.org/docs.html)
- [SQLite FTS5](https://sqlite.org/fts5.html)
- [SQLite JSON Functions](https://sqlite.org/json1.html)
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)
