-- One-time copy of industry catalog rows from the legacy `professions` table
-- into the unified `tags` table.
--
-- Industry is a flat-kind tag: every row carries parent_subject_group=NULL
-- (no leaf/group hierarchy, unlike skill/position/topic). Reads go through
-- TagService; ProfessionService and the `professions` table stay in place
-- until the frontend cuts over to /tags (Tracker #249, then cleanup in #233).
--
-- Idempotent via uq_tags_canonical (kind, subject_group, language, subject) —
-- safe to re-run.

INSERT INTO tags (kind, subject_group, "language", "subject", "desc", parent_subject_group)
SELECT
    'industry',
    p.subject_group,
    p."language",
    COALESCE(p."subject", ''),
    p.profession_metadata,
    NULL
FROM professions p
WHERE p.category = 'INDUSTRY'
ON CONFLICT ON CONSTRAINT uq_tags_canonical DO NOTHING;
