-- Phase 4 of mentor_schedules rrule refactor.
-- Backfills existing rows so they all use the new
-- (block, meeting_duration_minutes) representation. After this:
--   * rrule is NULL on every row that previously held FREQ=MINUTELY
--   * dtend means "block end" everywhere
--   * meeting_duration_minutes is non-NULL on every row
-- Phase 5 (true weekly recurrence) is then free to use rrule for its
-- intended purpose without colliding with sub-slot semantics.
--
-- IDEMPOTENT — only touches rows where meeting_duration_minutes IS NULL.
-- Apply with:
--   docker compose exec db psql -U postgres -v ON_ERROR_STOP=1 \
--     -f /path/to/2026-05-backfill-meeting-duration-minutes.sql
--
-- Run AFTER 2026-05-add-meeting-duration-minutes.sql (the column must exist).

\set ON_ERROR_STOP on

\echo
\echo '== before backfill =='
SELECT
  COUNT(*) FILTER (WHERE meeting_duration_minutes IS NULL) AS legacy_rows,
  COUNT(*) FILTER (WHERE meeting_duration_minutes IS NOT NULL) AS new_format_rows,
  COUNT(*) FILTER (WHERE rrule IS NOT NULL AND upper(rrule) LIKE '%FREQ=MINUTELY%') AS minutely_rrule_rows
FROM "x-career-dev".mentor_schedules;

-- Case 1: legacy MINUTELY-rrule rows. dtend currently holds the FIRST sub-slot
-- end (= dtstart + INTERVAL*60); rewrite to block end (= dtstart + INTERVAL*COUNT*60),
-- clear the rrule, and set meeting_duration_minutes from INTERVAL.
WITH parsed AS (
  SELECT
    id,
    dtstart,
    NULLIF(substring(rrule FROM 'INTERVAL=([0-9]+)'), '')::int AS interval_min,
    NULLIF(substring(rrule FROM 'COUNT=([0-9]+)'), '')::int    AS occurrence_count
  FROM "x-career-dev".mentor_schedules
  WHERE meeting_duration_minutes IS NULL
    AND rrule IS NOT NULL
    AND upper(rrule) LIKE '%FREQ=MINUTELY%'
),
valid AS (
  SELECT * FROM parsed
  WHERE interval_min IS NOT NULL
    AND interval_min > 0
    AND occurrence_count IS NOT NULL
    AND occurrence_count > 0
)
UPDATE "x-career-dev".mentor_schedules ms
SET
  dtend = v.dtstart + v.interval_min * v.occurrence_count * 60,
  rrule = NULL,
  meeting_duration_minutes = v.interval_min,
  updated_at = EXTRACT(EPOCH FROM NOW())::bigint
FROM valid v
WHERE ms.id = v.id;

-- Case 2: legacy single-slot rows (no rrule, dtend already = block end because
-- the block IS one meeting). Just stamp meeting_duration_minutes from the
-- existing slot length so the row reads as new format. Skip rows whose length
-- isn't a whole number of minutes — those would be data errors and should be
-- looked at by hand.
UPDATE "x-career-dev".mentor_schedules
SET
  meeting_duration_minutes = (dtend - dtstart) / 60,
  updated_at = EXTRACT(EPOCH FROM NOW())::bigint
WHERE meeting_duration_minutes IS NULL
  AND rrule IS NULL
  AND (dtend - dtstart) > 0
  AND (dtend - dtstart) % 60 = 0;

\echo
\echo '== after backfill =='
SELECT
  COUNT(*) FILTER (WHERE meeting_duration_minutes IS NULL) AS legacy_rows_remaining,
  COUNT(*) FILTER (WHERE meeting_duration_minutes IS NOT NULL) AS new_format_rows,
  COUNT(*) FILTER (WHERE rrule IS NOT NULL AND upper(rrule) LIKE '%FREQ=MINUTELY%') AS minutely_rrule_rows_remaining
FROM "x-career-dev".mentor_schedules;

\echo
\echo '== rows still legacy (need manual review) =='
SELECT id, user_id, dt_type, dtstart, dtend, rrule, exdate
FROM "x-career-dev".mentor_schedules
WHERE meeting_duration_minutes IS NULL
ORDER BY id
LIMIT 20;
