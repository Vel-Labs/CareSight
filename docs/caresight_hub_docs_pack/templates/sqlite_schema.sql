PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    relationship TEXT,
    phone TEXT,
    facetime_handle TEXT,
    access_level TEXT NOT NULL DEFAULT 'standard',
    active_until TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    subject_type TEXT NOT NULL CHECK(subject_type IN ('person','pet','anonymous')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cameras (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_uri TEXT,
    room TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    polygon_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(camera_id) REFERENCES cameras(id)
);

CREATE TABLE IF NOT EXISTS routines (
    id TEXT PRIMARY KEY,
    subject_id TEXT,
    name TEXT NOT NULL,
    expected_window_start TEXT,
    expected_window_end TEXT,
    required_evidence_json TEXT,
    escalation_policy_id TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    subject_id TEXT,
    camera_id TEXT NOT NULL,
    zone_id TEXT,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    confidence_label TEXT NOT NULL,
    evidence_json TEXT,
    recommended_actions_json TEXT,
    status TEXT NOT NULL DEFAULT 'observed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(camera_id) REFERENCES cameras(id),
    FOREIGN KEY(zone_id) REFERENCES zones(id)
);

CREATE TABLE IF NOT EXISTS event_observations (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    object_class TEXT NOT NULL,
    confidence REAL,
    bbox_json TEXT,
    tracker_id TEXT,
    metadata_json TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id TEXT PRIMARY KEY,
    journal_date TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    source_event_id TEXT,
    confirmation_status TEXT DEFAULT 'awaiting_confirmation',
    confirmed_by TEXT,
    confirmed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(source_event_id) REFERENCES events(id),
    FOREIGN KEY(confirmed_by) REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    recipient_person_id TEXT,
    channel TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_at TEXT,
    acknowledged_at TEXT,
    outcome TEXT,
    metadata_json TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(recipient_person_id) REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    actor_id TEXT,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT,
    FOREIGN KEY(actor_id) REFERENCES people(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS journal_fts USING fts5(
    title,
    body,
    content='journal_entries',
    content_rowid='rowid'
);
