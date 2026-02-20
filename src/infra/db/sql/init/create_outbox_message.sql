CREATE TYPE aggregate_type_enum AS ENUM (
  'USER',
);

CREATE TYPE event_type_enum AS ENUM (
  'USER_CREATED',
  'USER_UPDATED',
  'USER_DELETED'
);
-- This is used for all messages routing to different server
CREATE TABLE outbox_message (
  id              BIGSERIAL PRIMARY KEY,
  aggregate_id    VARCHAR(100) NOT NULL,    -- e.g. 'user_id'
  aggregate_type  aggregate_type_enum NOT NULL,
  event_type      event_type_enum NOT NULL,
  payload         JSONB NOT NULL,           -- message body
  status          INT NOT NULL DEFAULT '0', -- 0: initial, 1: pending, 2: failed, 3: success
  retry_count     INT NOT NULL DEFAULT 0,
  err_msg         TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  next_retry_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);