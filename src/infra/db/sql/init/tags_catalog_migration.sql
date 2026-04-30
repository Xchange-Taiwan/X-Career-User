-- Catalog mirror for #228: copy v1 catalog rows into the unified `tags` table.
-- Idempotent: re-runnable, ON CONFLICT DO NOTHING dedupes by canonical key.
--
-- Sources mirrored (4 of 5 kinds — `what_i_offer` has no catalog and is
-- populated by user writes in #229+):
--   interests(category='INTERESTED_POSITION') -> tags(kind='position')
--   interests(category='SKILL')               -> tags(kind='skill')
--   interests(category='TOPIC')               -> tags(kind='topic')
--   professions(category='EXPERTISE')         -> tags(kind='expertise')
--
-- Not mirrored:
--   professions(category='INDUSTRY') — industry stays in profiles.industry
--   (see #226 epic; not part of the tag matching dimension).
--
-- Verify after running:
--   SELECT kind, COUNT(*) FROM tags GROUP BY kind ORDER BY kind;

INSERT INTO tags (kind, subject_group, "language", "subject", "desc")
SELECT
    CASE category
        WHEN 'INTERESTED_POSITION' THEN 'position'
        WHEN 'SKILL'               THEN 'skill'
        WHEN 'TOPIC'               THEN 'topic'
    END AS kind,
    subject_group,
    "language",
    COALESCE("subject", '') AS "subject",
    "desc"
FROM interests
WHERE category IN ('INTERESTED_POSITION', 'SKILL', 'TOPIC')
ON CONFLICT (kind, subject_group, "language", "subject") DO NOTHING;


INSERT INTO tags (kind, subject_group, "language", "subject", "desc")
SELECT
    'expertise' AS kind,
    subject_group,
    "language",
    COALESCE("subject", '') AS "subject",
    profession_metadata AS "desc"
FROM professions
WHERE category = 'EXPERTISE'
ON CONFLICT (kind, subject_group, "language", "subject") DO NOTHING;
