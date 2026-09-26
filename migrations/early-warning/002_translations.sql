BEGIN;
CREATE TABLE translations (
    translation_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL REFERENCES observations(observation_id),
    revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(observation_id, revision)
);
PRAGMA user_version = 2;
COMMIT;
