-- Foundation schema for the unified tag model.
--
-- User selections are stored directly on profiles.want_tags / profiles.have_tags
-- (see profiles ORM), keyed by subject_group; the catalog below maps each
-- subject_group to its kind and display metadata.

CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY,
    kind VARCHAR(20) NOT NULL,
    subject_group VARCHAR(40),
    "language" VARCHAR(10),
    "subject" TEXT NOT NULL DEFAULT '',
    "desc" JSONB,
    -- NULL ⇔ group row (catalog scaffolding); NOT NULL ⇔ leaf row.
    -- Strict invariant — _validate_leaves rejects writes that would
    -- create orphan leaves (no parent), so this single column is enough
    -- to tell groups and leaves apart.
    parent_subject_group VARCHAR(40),
    CONSTRAINT uq_tags_canonical UNIQUE (kind, subject_group, "language", "subject")
);

CREATE INDEX IF NOT EXISTS idx_tags_kind ON tags(kind);
CREATE INDEX IF NOT EXISTS ix_tags_parent_subject_group ON tags(parent_subject_group);
