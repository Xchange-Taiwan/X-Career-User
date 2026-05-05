-- Phase 1 of mentor_schedules rrule refactor.
-- Adds meeting_duration_minutes column so (dtstart, dtend) can mean
-- "block start/end" with sub-slot length carried in this column,
-- instead of the FREQ=MINUTELY rrule abuse. NULL on existing rows
-- means "still legacy format" — Phase 4 backfills them.
--
-- Idempotent: re-runnable. Apply with:
--   docker compose exec db psql -U postgres -v ON_ERROR_STOP=1 \
--     -f /path/to/2026-05-add-meeting-duration-minutes.sql

\set ON_ERROR_STOP on

ALTER TABLE "x-career-dev".mentor_schedules
    ADD COLUMN IF NOT EXISTS meeting_duration_minutes INT;

COMMENT ON COLUMN "x-career-dev".mentor_schedules.meeting_duration_minutes IS
    'New-format flag. NULL = legacy MINUTELY-rrule row; set = (dtstart,dtend) is block, divided into sub-slots of this length.';
