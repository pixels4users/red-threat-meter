CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    logical_key TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fetches (
    seq INTEGER PRIMARY KEY,
    observation_id TEXT NOT NULL REFERENCES observations(observation_id),
    fetched_at TEXT NOT NULL,
    run_id TEXT NOT NULL,
    raw_refs TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS fetches_time ON fetches(fetched_at, observation_id);
CREATE TABLE IF NOT EXISTS source_checks (
    seq INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL REFERENCES observations(observation_id),
    revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(observation_id, revision)
);
CREATE TABLE IF NOT EXISTS releases (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
PRAGMA user_version = 1;
