-- Design v1.0, 2026-11-05. Reference schema, not a migration for the existing demo.
-- Build immutable database generations; publish only after integrity/coverage checks.
PRAGMA foreign_keys = ON;

CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    revision TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL CHECK(length(artifact_sha256)=64),
    local_path TEXT NOT NULL,
    license_json TEXT NOT NULL CHECK(json_valid(license_json)),
    metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json))
);

CREATE TABLE source_units (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    locator_json TEXT NOT NULL CHECK(json_valid(locator_json)),
    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    content_sha256 TEXT NOT NULL CHECK(length(content_sha256)=64),
    namespace TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    verification_json TEXT NOT NULL CHECK(json_valid(verification_json))
);
CREATE INDEX source_units_by_source ON source_units(source_id);
CREATE INDEX source_units_by_hash ON source_units(content_sha256);

CREATE TABLE concepts (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE concept_aliases (
    alias TEXT NOT NULL,
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    relation TEXT NOT NULL CHECK(relation IN ('simplified_variant','traditional_variant','synonym','related')),
    PRIMARY KEY(alias, concept_id, relation)
) WITHOUT ROWID;

CREATE TABLE statements (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK(kind IN ('definition','conditional_rule','method','interpretation','conflict')),
    title TEXT NOT NULL,
    statement_text TEXT NOT NULL,
    topic TEXT NOT NULL,
    namespace TEXT NOT NULL,
    school TEXT NOT NULL,
    applicability_scope TEXT NOT NULL CHECK(applicability_scope IN ('general','conditional','case_specific','unknown')),
    conditions_json TEXT CHECK(conditions_json IS NULL OR json_valid(conditions_json)),
    exceptions_json TEXT CHECK(exceptions_json IS NULL OR json_valid(exceptions_json)),
    review_status TEXT NOT NULL CHECK(review_status IN ('candidate','reviewed','rejected')),
    verification_json TEXT NOT NULL CHECK(json_valid(verification_json))
);
CREATE TABLE statement_sources (
    statement_id TEXT NOT NULL REFERENCES statements(id),
    source_unit_id TEXT NOT NULL REFERENCES source_units(id),
    relation TEXT NOT NULL CHECK(relation IN ('quote','supports','contradicts','context')),
    PRIMARY KEY(statement_id, source_unit_id, relation)
) WITHOUT ROWID;
CREATE TABLE statement_concepts (
    statement_id TEXT NOT NULL REFERENCES statements(id),
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    PRIMARY KEY(statement_id, concept_id)
) WITHOUT ROWID;

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    stable_id TEXT NOT NULL UNIQUE,
    source_unit_id TEXT REFERENCES source_units(id),
    statement_id TEXT REFERENCES statements(id),
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    title_terms TEXT NOT NULL,
    body_terms TEXT NOT NULL,
    namespace TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    eligible INTEGER NOT NULL CHECK(eligible IN (0,1)),
    content_sha256 TEXT NOT NULL CHECK(length(content_sha256)=64),
    metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json)),
    CHECK(source_unit_id IS NOT NULL OR statement_id IS NOT NULL)
);
CREATE INDEX chunks_by_scope ON chunks(namespace,eligible);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    title_terms, body_terms, content='chunks', content_rowid='id', tokenize='unicode61'
);
-- title_terms/body_terms are pre-tokenized using OpenCC + domain terms + CJK bigrams.
-- Rebuild this derived index inside the unpublished generation after ingestion.

CREATE TABLE executable_rule_adapters (
    id TEXT PRIMARY KEY,
    implementation_path TEXT NOT NULL,
    engine_revision TEXT NOT NULL,
    source_unit_id TEXT NOT NULL REFERENCES source_units(id),
    input_profile_json TEXT NOT NULL CHECK(json_valid(input_profile_json)),
    validation_status TEXT NOT NULL CHECK(validation_status IN ('unvalidated','tested','disabled'))
);

CREATE TABLE vector_generations (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_revision TEXT NOT NULL,
    dimensions INTEGER NOT NULL CHECK(dimensions > 0),
    dtype TEXT NOT NULL CHECK(dtype='float32'),
    normalized INTEGER NOT NULL CHECK(normalized=1),
    vector_path TEXT NOT NULL,
    row_ids_path TEXT NOT NULL,
    manifest_json TEXT NOT NULL CHECK(json_valid(manifest_json))
);

CREATE TABLE build_runs (
    id TEXT PRIMARY KEY,
    builder_revision TEXT NOT NULL,
    sources_manifest_json TEXT NOT NULL CHECK(json_valid(sources_manifest_json)),
    component_versions_json TEXT NOT NULL CHECK(json_valid(component_versions_json)),
    coverage_json TEXT NOT NULL CHECK(json_valid(coverage_json)),
    status TEXT NOT NULL CHECK(status IN ('staging','validated','published','failed'))
);
