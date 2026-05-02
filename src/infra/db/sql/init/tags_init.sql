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
    -- NULL on group rows AND on orphan leaves; non-NULL on linked leaves.
    parent_subject_group VARCHAR(40),
    -- Distinguishes real group rows from orphan leaves (parent_subject_group
    -- is NULL on both); needed for leaf-only validation and catalog grouping.
    is_group BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_tags_canonical UNIQUE (kind, subject_group, "language", "subject")
);

CREATE INDEX IF NOT EXISTS idx_tags_kind ON tags(kind);
CREATE INDEX IF NOT EXISTS ix_tags_parent_subject_group ON tags(parent_subject_group);
