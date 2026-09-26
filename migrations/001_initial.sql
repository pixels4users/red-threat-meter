CREATE TABLE materials (
    material_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(document_id, content_hash)
);
CREATE INDEX materials_document ON materials(document_id, fetched_at);
CREATE TABLE observations (
    document_id TEXT NOT NULL,
    material_id TEXT NOT NULL REFERENCES materials(material_id),
    observed_at TEXT NOT NULL,
    UNIQUE(document_id, material_id, observed_at)
);
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL UNIQUE REFERENCES materials(material_id),
    payload TEXT NOT NULL
);
CREATE TABLE incident_revisions (
    revision_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK(revision >= 1),
    recorded_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(incident_id, revision)
);
CREATE TABLE resolutions (
    resolution_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
    recorded_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    error TEXT
);
CREATE TABLE snapshots (
    run_id TEXT PRIMARY KEY REFERENCES runs(run_id),
    as_of TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE source_checks (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(run_id, source_id)
);
PRAGMA user_version = 1;
