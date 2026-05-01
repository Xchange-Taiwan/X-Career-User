-- Foundation schema for the unified tag model (#226 / #228).
-- Additive only: no existing table is modified or referenced for write here.
-- Run after user_init.sql (this file does not depend on it for DDL,
-- but the catalog mirror script tags_catalog_migration.sql does).

CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY,
    kind VARCHAR(20) NOT NULL,
    subject_group VARCHAR(40),
    "language" VARCHAR(10),
    "subject" TEXT NOT NULL DEFAULT '',
    "desc" JSONB,
    -- Two-layer hierarchy (#226): NULL on top-level group rows AND on
    -- auto-created orphan leaves; non-NULL on properly-linked leaf rows.
    parent_subject_group VARCHAR(40),
    -- TRUE on real catalog group rows, FALSE on leaves and orphans. Needed
    -- because parent_subject_group=NULL alone can't distinguish a real group
    -- from an orphan leaf (which broke replace_user_tags / get_catalog).
    is_group BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_tags_canonical UNIQUE (kind, subject_group, "language", "subject")
);

CREATE INDEX IF NOT EXISTS idx_tags_kind ON tags(kind);
CREATE INDEX IF NOT EXISTS ix_tags_parent_subject_group ON tags(parent_subject_group);


CREATE TABLE IF NOT EXISTS user_tags (
    user_id BIGINT NOT NULL,
    tag_id BIGINT NOT NULL,
    intent VARCHAR(10) NOT NULL,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    PRIMARY KEY (user_id, tag_id, intent)
);

CREATE INDEX IF NOT EXISTS idx_user_tags_tag_intent ON user_tags(tag_id, intent);
