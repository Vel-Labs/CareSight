CREATE TABLE IF NOT EXISTS cameras (
  camera_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_uri TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  fps INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS zones (
  zone_id TEXT PRIMARY KEY,
  camera_id TEXT NOT NULL REFERENCES cameras(camera_id),
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  x_min REAL NOT NULL,
  y_min REAL NOT NULL,
  x_max REAL NOT NULL,
  y_max REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS event_policies (
  policy_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  dwell_seconds REAL NOT NULL,
  severity TEXT NOT NULL,
  confidence TEXT NOT NULL,
  requires_human_confirmation INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  camera_id TEXT NOT NULL REFERENCES cameras(camera_id),
  zone_id TEXT REFERENCES zones(zone_id),
  severity TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  requires_human_confirmation INTEGER NOT NULL,
  allowed_actions_json TEXT NOT NULL,
  blocked_actions_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_observations (
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  observed_at TEXT NOT NULL,
  class_name TEXT NOT NULL,
  confidence REAL NOT NULL,
  bbox_json TEXT NOT NULL,
  track_id TEXT,
  zone_id TEXT REFERENCES zones(zone_id)
);

CREATE TABLE IF NOT EXISTS event_reviews (
  review_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  reviewer TEXT NOT NULL,
  decision TEXT NOT NULL CHECK(decision IN ('human_confirmed', 'dismissed', 'needs_followup')),
  note TEXT,
  reviewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entries (
  journal_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  entry_type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_handoffs (
  handoff_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  target_framework TEXT NOT NULL,
  purpose TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
