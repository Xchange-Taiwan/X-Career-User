CREATE TABLE IF NOT EXISTS profiles (
    user_id BIGSERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    avatar TEXT DEFAULT '',
    "location" TEXT DEFAULT '',
    "job_title" TEXT DEFAULT '',
    linkedin_profile TEXT DEFAULT '',
    personal_statement TEXT DEFAULT '',
    about TEXT DEFAULT '',
    company TEXT DEFAULT '',
    seniority_level VARCHAR(20),
    years_of_experience VARCHAR DEFAULT 0,
    industry TEXT,
    interested_positions JSONB,
    skills JSONB,
    topics JSONB,
    expertises JSONB,
    "language" VARCHAR(10),
    is_mentor BOOLEAN DEFAULT FALSE,
    -- Mentor tag selections, flat subject_group arrays. Kind comes from the
    -- tags catalog (JOIN at read time buckets these into the 5 API fields).
    want_tags TEXT[] NOT NULL DEFAULT '{}',
    have_tags TEXT[] NOT NULL DEFAULT '{}',
    -- Inline experiences batch — replaces the standalone mentor_experiences
    -- table. Each element is {category, order, mentor_experiences_metadata};
    -- every PUT /mentors/mentor_profile overwrites the column wholesale.
    experiences JSONB NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT ck_profiles_seniority_level CHECK (
        seniority_level IN (
            'NO REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER'
        )
    )
);


CREATE TABLE IF NOT EXISTS mentor_schedules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,    -- user ID, used to distinguish users
    dt_type VARCHAR(20) NOT NULL,
    dt_year INT NOT NULL,       -- dt_year of the event
    dt_month INT NOT NULL,      -- dt_month of the event
    dtstart BIGINT NOT NULL,    -- start timestamp of the event
    dtend BIGINT NOT NULL,      -- end timestamp of the event
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC', -- timezone, for example: 'America/New_York'
    rrule TEXT,                 -- rule for repeating events, for example: 'FREQ=WEEKLY;COUNT=4'
    exdate JSONB DEFAULT '[]'::jsonb,   -- list of excluded dates/timestamps (ISO format)
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    CONSTRAINT ck_mentor_schedules_dt_type CHECK (
        dt_type IN ('ALLOW', 'FORBIDDEN')
    )
);

CREATE INDEX IF NOT EXISTS idx_mentor_schedules_user_id
    ON mentor_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_schedules_user_event_time
    ON mentor_schedules(user_id, dtstart, dtend);
CREATE INDEX IF NOT EXISTS idx_montor_schedules_user_year_month
    ON mentor_schedules(user_id, dt_year, dt_month);


CREATE TABLE IF NOT EXISTS canned_messages (
    "id" SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    "role" VARCHAR(20) NOT NULL,
    MESSAGE TEXT,
    CONSTRAINT ck_canned_messages_role CHECK (
        "role" IN ('MENTOR', 'MENTEE')
    )
    --,CONSTRAINT fk_profiles_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);

CREATE TABLE IF NOT EXISTS reservations (
    "id" SERIAL PRIMARY KEY,
    schedule_id INT NOT NULL,
    dtstart BIGINT NOT NULL,
    dtend BIGINT NOT NULL,
    my_user_id BIGINT NOT NULL,    -- sharding key: my_user_id
    my_status VARCHAR(20) NOT NULL,
    my_role VARCHAR(20) NULL,
    user_id BIGINT NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "messages" JSONB DEFAULT '[]'::jsonb,
    previous_reserve JSONB,  -- previous [schedule_id + dtstart],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_reservations_my_status CHECK (
        my_status IN ('ACCEPT', 'PENDING', 'REJECT')
    ),
    CONSTRAINT ck_reservations_my_role CHECK (
        my_role IS NULL OR my_role IN ('MENTOR', 'MENTEE')
    ),
    CONSTRAINT ck_reservations_status CHECK (
        "status" IN ('ACCEPT', 'PENDING', 'REJECT')
    )
);

-- Partial unique: only enforce uniqueness for non-cancelled reservations.
-- Cancellations leave a REJECT row behind; without WHERE, re-booking the
-- same slot fails the unique constraint even though find_active_duplicate
-- (reservation_repository.py) already excludes REJECT at the app layer.
CREATE UNIQUE INDEX IF NOT EXISTS uidx_reservation_active_user_dtstart_dtend_schedule_id_user_id
    ON reservations(my_user_id, dtstart, dtend, schedule_id, user_id)
    WHERE my_status <> 'REJECT' AND "status" <> 'REJECT';
CREATE INDEX IF NOT EXISTS idx_reservation_user_my_status_status_dtend
    ON reservations(my_user_id, my_status, "status", dtend);
CREATE INDEX IF NOT EXISTS idx_reservation_user_my_status_dtstart_dtend
    ON reservations(my_user_id, my_status, dtstart, dtend);


CREATE TABLE IF NOT EXISTS interests (
    "id" SERIAL PRIMARY KEY,
    category VARCHAR(40),
    subject_group VARCHAR(40),
    "language" VARCHAR(10),
    "subject" TEXT DEFAULT '',
    "desc" JSONB,
    CONSTRAINT ck_interests_category CHECK (
        category IS NULL OR category IN ('INTERESTED_POSITION', 'SKILL', 'TOPIC')
    )
);

CREATE TABLE IF NOT EXISTS activities (
    "id" VARCHAR(255) PRIMARY KEY,
    mentor_reservation_id INT NOT NULL,
    mentee_reservation_id INT NOT NULL,
    "service" VARCHAR(20) NOT NULL DEFAULT 'GOOGLE',
    "status" VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_activities_service CHECK (
        "service" IN ('GOOGLE')
    ),
    CONSTRAINT ck_activities_status CHECK (
        "status" IN ('SCHEDULED', 'CANCELLED')
    )
);

CREATE INDEX IF NOT EXISTS idx_activities_mentor_reservation_id
    ON activities(mentor_reservation_id);
CREATE INDEX IF NOT EXISTS idx_activities_mentee_reservation_id
    ON activities(mentee_reservation_id);
