CREATE TABLE IF NOT EXISTS appearance_profiles (
  appearance_profile_id TEXT PRIMARY KEY,
  active_date TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  descriptor_source TEXT NOT NULL CHECK(descriptor_source IN (
    'runtime_observation',
    'seeded_test_fixture',
    'operator_demo_seed'
  )),
  descriptor_status TEXT NOT NULL CHECK(descriptor_status IN (
    'available',
    'posture_limited',
    'unavailable',
    'unreadable',
    'invalid_bbox'
  )),
  source_event_id TEXT,
  source_observation_id INTEGER,
  snapshot_path TEXT,
  frame_source TEXT,
  last_seen_at TEXT,
  last_seen_camera_id TEXT,
  last_seen_room TEXT,
  role_assignment TEXT NOT NULL,
  assignment_source TEXT NOT NULL,
  assigned_by TEXT,
  assigned_at TEXT,
  attributes_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appearance_profiles_active
  ON appearance_profiles(active_date, expires_at, appearance_profile_id);

CREATE INDEX IF NOT EXISTS idx_appearance_profiles_source_event
  ON appearance_profiles(source_event_id);

CREATE TABLE IF NOT EXISTS appearance_profile_observations (
  profile_observation_id TEXT PRIMARY KEY,
  appearance_profile_id TEXT NOT NULL REFERENCES appearance_profiles(appearance_profile_id) ON DELETE CASCADE,
  observed_at TEXT NOT NULL,
  camera_id TEXT,
  room TEXT,
  track_id TEXT,
  source_event_id TEXT,
  source_observation_id INTEGER,
  snapshot_path TEXT,
  frame_source TEXT,
  descriptor_source TEXT NOT NULL CHECK(descriptor_source IN (
    'runtime_observation',
    'seeded_test_fixture',
    'operator_demo_seed'
  )),
  descriptor_status TEXT NOT NULL CHECK(descriptor_status IN (
    'available',
    'posture_limited',
    'unavailable',
    'unreadable',
    'invalid_bbox'
  )),
  confidence REAL,
  attributes_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_observations_profile
  ON appearance_profile_observations(appearance_profile_id, observed_at, profile_observation_id);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_observations_event
  ON appearance_profile_observations(source_event_id);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_observations_track
  ON appearance_profile_observations(track_id);

CREATE TABLE IF NOT EXISTS appearance_profile_samples (
  sample_id TEXT PRIMARY KEY,
  appearance_profile_id TEXT NOT NULL,
  active_date TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  camera_id TEXT,
  room TEXT,
  track_id TEXT,
  source_event_id TEXT,
  source_observation_id INTEGER,
  snapshot_path TEXT NOT NULL,
  frame_source TEXT NOT NULL,
  descriptor_status TEXT NOT NULL CHECK(descriptor_status IN (
    'available',
    'posture_limited',
    'unavailable',
    'unreadable',
    'invalid_bbox'
  )),
  quality_score REAL NOT NULL,
  quality_reasons_json TEXT NOT NULL,
  detection_confidence REAL,
  bbox_json TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  retained_rank INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_samples_profile
  ON appearance_profile_samples(appearance_profile_id, quality_score DESC, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_samples_active_date
  ON appearance_profile_samples(active_date, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_appearance_profile_samples_event
  ON appearance_profile_samples(source_event_id);
