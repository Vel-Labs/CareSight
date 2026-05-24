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

CREATE TABLE IF NOT EXISTS observation_checks (
  check_id TEXT PRIMARY KEY,
  check_type TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL,
  camera_id TEXT NOT NULL REFERENCES cameras(camera_id),
  zone_id TEXT REFERENCES zones(zone_id),
  status TEXT NOT NULL CHECK(status IN ('no_event_persisted', 'event_persisted', 'blocked')),
  frame_count INTEGER NOT NULL,
  elapsed_seconds REAL NOT NULL,
  required_dwell_seconds REAL,
  event_id TEXT REFERENCES events(event_id),
  result_json TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS agent_drafts (
  draft_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  provider TEXT NOT NULL,
  purpose TEXT NOT NULL,
  validation_status TEXT NOT NULL CHECK(validation_status IN ('validated', 'blocked')),
  draft_text TEXT NOT NULL,
  safe_rewrite TEXT,
  blocked_claims_json TEXT NOT NULL,
  safety_boundaries_json TEXT NOT NULL,
  provenance_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_action_requests (
  request_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  requested_action TEXT NOT NULL,
  stage TEXT NOT NULL CHECK(stage = 'staged'),
  execution_state TEXT NOT NULL CHECK(execution_state = 'not_executed'),
  requires_human_approval INTEGER NOT NULL,
  source_draft_id TEXT NOT NULL REFERENCES agent_drafts(draft_id) ON DELETE CASCADE,
  destination TEXT,
  escalation_level TEXT NOT NULL DEFAULT 'attention',
  recipient_role TEXT,
  allowed_contact_ids_json TEXT NOT NULL DEFAULT '[]',
  response_options_json TEXT NOT NULL DEFAULT '[]',
  safety_boundaries_json TEXT NOT NULL,
  provenance_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_execution_attempts (
  attempt_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES agent_action_requests(request_id) ON DELETE CASCADE,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  harness TEXT NOT NULL,
  attempt_kind TEXT NOT NULL CHECK(attempt_kind IN ('dry_run', 'live')),
  execution_state TEXT NOT NULL CHECK(execution_state IN ('pending_execution', 'dry_run', 'blocked', 'executed', 'failed')),
  result TEXT NOT NULL,
  error TEXT,
  external_action_performed INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  safety_boundaries_json TEXT NOT NULL,
  provenance_json TEXT NOT NULL
);
