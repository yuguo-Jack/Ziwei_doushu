-- One immutable SQLite shard per dataset version and Gregorian birth year.
PRAGMA foreign_keys=ON;

CREATE TABLE dataset_profile (
    dataset_tag TEXT PRIMARY KEY,
    content_version TEXT NOT NULL,
    source_archive_sha256 TEXT NOT NULL CHECK(length(source_archive_sha256)=64),
    year INTEGER NOT NULL,
    profile_json TEXT NOT NULL CHECK(json_valid(profile_json)),
    expected_cases INTEGER NOT NULL,
    expected_readings INTEGER NOT NULL,
    coverage_status TEXT NOT NULL CHECK(coverage_status IN ('staging','validated'))
);

CREATE TABLE text_blocks (
    id INTEGER PRIMARY KEY,
    sha256 BLOB NOT NULL UNIQUE CHECK(length(sha256)=32),
    exact_text TEXT NOT NULL
);
CREATE TABLE topic_texts (
    id INTEGER PRIMARY KEY,
    sha256 BLOB NOT NULL UNIQUE CHECK(length(sha256)=32),
    layout_zstd BLOB NOT NULL,
    chars INTEGER NOT NULL CHECK(chars>=0),
    utf8_bytes INTEGER NOT NULL CHECK(utf8_bytes>=0)
);
-- layout_zstd contains a zstd-compressed JSON integer array of text_blocks.id.
-- Delimiters, line breaks, whitespace and ordering are preserved exactly.

CREATE TABLE cases (
    id INTEGER PRIMARY KEY,
    birth_key TEXT NOT NULL UNIQUE,
    y INTEGER NOT NULL,
    m INTEGER NOT NULL CHECK(m BETWEEN 1 AND 12),
    d INTEGER NOT NULL CHECK(d BETWEEN 1 AND 31),
    h INTEGER NOT NULL CHECK(h BETWEEN 0 AND 11),
    g TEXT NOT NULL CHECK(g IN ('male','female')),
    metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json)),
    UNIQUE(y,m,d,h,g)
);
-- The importer additionally validates real calendar dates and the complete key.
CREATE TABLE case_topics (
    case_id INTEGER NOT NULL REFERENCES cases(id),
    topic TEXT NOT NULL CHECK(topic IN (
        'overview','personality','love','career','wealth','health','family',
        'children','move','friends','home','spirit','parents')),
    text_id INTEGER NOT NULL REFERENCES topic_texts(id),
    PRIMARY KEY(case_id,topic)
) WITHOUT ROWID;
