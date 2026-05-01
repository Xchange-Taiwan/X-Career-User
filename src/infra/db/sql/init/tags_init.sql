-- Foundation schema for the unified tag model.

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


CREATE TABLE IF NOT EXISTS user_tags (
    user_id BIGINT NOT NULL,
    tag_id BIGINT NOT NULL,
    intent VARCHAR(10) NOT NULL,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    PRIMARY KEY (user_id, tag_id, intent)
);

CREATE INDEX IF NOT EXISTS idx_user_tags_tag_intent ON user_tags(tag_id, intent);
