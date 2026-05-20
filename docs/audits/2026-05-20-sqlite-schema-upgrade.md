# SQLite Schema Upgrade Audit

Date: 2026-05-20

## Scope

This audit records the non-destructive schema upgrade for existing local SQLite databases.

## Finding

Existing `caresight-v0.sqlite3` files created before the tracking sprint can have `event_observations` without the new `track_id` column. `CREATE TABLE IF NOT EXISTS` does not add columns to existing tables.

## Implemented

- `SQLiteStore.initialize()` now ensures `event_observations.track_id` exists.
- The upgrade uses additive `ALTER TABLE` and does not delete existing rows.
- Regression coverage creates a legacy table, inserts an observation, initializes the store, and verifies the row remains.

## Validation

Run:

```bash
npm run py:check
npm run check
```
