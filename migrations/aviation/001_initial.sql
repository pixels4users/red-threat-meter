BEGIN;
CREATE TABLE samples (
    sample_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX samples_time ON samples(finished_at);
CREATE TABLE releases (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
PRAGMA user_version = 1;
COMMIT;
