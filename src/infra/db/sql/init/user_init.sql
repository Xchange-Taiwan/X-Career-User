DO $$ 
BEGIN
    -- 如果 'SENIORITY_LEVEL' 類型不存在，則創建它
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'seniority_level') THEN
        CREATE TYPE SENIORITY_LEVEL AS ENUM('NO_REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER');
    END IF;
    -- 重複此操作來處理其他類型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interest_category') THEN
        CREATE TYPE INTEREST_CATEGORY AS ENUM('INTERESTED_POSITION', 'SKILL', 'TOPIC');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'profession_category') THEN
        CREATE TYPE PROFESSION_CATEGORY AS ENUM('EXPERTISE', 'INDUSTRY');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'experience_category') THEN
        CREATE TYPE EXPERIENCE_CATEGORY AS ENUM('WORK', 'EDUCATION', 'LINK');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'schedule_type') THEN
        CREATE TYPE SCHEDULE_TYPE AS ENUM('ALLOW', 'FORBIDDEN');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_status') THEN
        CREATE TYPE BOOKING_STATUS AS ENUM('ACCEPT', 'PENDING', 'REJECT');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_type') THEN
        CREATE TYPE ROLE_TYPE AS ENUM('MENTOR', 'MENTEE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'industry_category') THEN
        CREATE TYPE INDUSTRY_CATEGORY AS ENUM('SOFTWARE', 'HARDWARE', 'SERVICE', 'FINANCE', 'OTHER');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_type') THEN
        CREATE TYPE ACCOUNT_TYPE AS ENUM('XC', 'GOOGLE', 'LINKEDIN');
    END IF;
END $$;


CREATE TABLE IF NOT EXISTS accounts (
    aid BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL, -- Email addresses are typically VARCHAR with a length constraint
    email2 VARCHAR(255),                -- Same for the secondary email address
    pass_hash VARCHAR(60),              -- Password hashes often have a fixed length (e.g., bcrypt is 60 characters)
    pass_salt VARCHAR(60),              -- Assuming the salt is a fixed-length string (e.g., bcrypt salts are often 29 characters)
    oauth_id VARCHAR(255),              -- OAuth IDs are usually strings but can have a variable length
    refresh_token VARCHAR(255),         -- Refresh tokens are usually strings but can have a variable length
    user_id BIGINT UNIQUE DEFAULT nextval('user_id_seq'),       -- Integer is fine for user IDs, keeping the UNIQUE constraint
    account_type ACCOUNT_TYPE,          -- Assuming 'account_type' is an ENUM or a custom type
    is_active BOOLEAN DEFAULT TRUE,     -- BOOLEAN is a more appropriate type for true/false values
    "region" VARCHAR(50),                 -- Regions are typically short strings, so VARCHAR(50) should suffice
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS profiles (
    user_id BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    avatar VARCHAR(255) DEFAULT '',
    "location" VARCHAR(100) DEFAULT '',
    "job_title" VARCHAR(255) DEFAULT '',
    personal_statement TEXT DEFAULT '',
    about TEXT DEFAULT '',
    company VARCHAR(255) DEFAULT '',
    seniority_level SENIORITY_LEVEL,
    years_of_experience VARCHAR(100) DEFAULT 0,
	industry VARCHAR(255),
    interested_positions JSONB,
    skills JSONB,
    topics JSONB,
    expertises JSONB,
    personal_links JSONB,
    education JSONB,
    work_experience JSONB,
    "language" VARCHAR(10)
);


CREATE TABLE IF NOT EXISTS mentor_experiences (
    "id" SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    category EXPERIENCE_CATEGORY NOT NULL,
    "order" INT NOT NULL,
    mentor_experiences_metadata JSONB
    --,CONSTRAINT fk_profile_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);


CREATE TABLE IF NOT EXISTS professions (
    "id" SERIAL PRIMARY KEY,
    category PROFESSION_CATEGORY ,
    subject_group VARCHAR(40),
    "language" VARCHAR(10),
    "subject" TEXT DEFAULT '',
    profession_metadata JSONB
);


CREATE TABLE IF NOT EXISTS mentor_schedules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,    -- user ID, used to distinguish users
    dt_type VARCHAR(20) NOT NULL CHECK (dt_type IN ('ALLOW', 'FORBIDDEN')), -- event type
    dt_year INT NOT NULL,       -- dt_year of the event
    dt_month INT NOT NULL,      -- dt_month of the event
    dtstart BIGINT NOT NULL,    -- start timestamp of the event
    dtend BIGINT NOT NULL,      -- end timestamp of the event
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC', -- timezone, for example: 'America/New_York'
    rrule TEXT,                 -- rule for repeating events, for example: 'FREQ=WEEKLY;COUNT=4'
    exdate JSONB DEFAULT '[]'::jsonb,   -- list of excluded dates/timestamps (ISO format)
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE INDEX idx_mentor_schedules_user_id ON mentor_schedules(user_id);
CREATE INDEX idx_mentor_schedules_user_event_time ON mentor_schedules(user_id, dtstart, dtend);
CREATE INDEX idx_montor_schedules_user_year_month ON mentor_schedules(user_id, dt_year, dt_month);


CREATE TABLE IF NOT EXISTS canned_messages (
    "id" SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    "role" ROLE_TYPE NOT NULL,
    MESSAGE TEXT
    --,CONSTRAINT fk_profiles_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);

CREATE TABLE IF NOT EXISTS reservations (
    "id" SERIAL PRIMARY KEY,
    schedule_id INT NOT NULL,
    dtstart BIGINT NOT NULL,
    dtend BIGINT NOT NULL,
    my_user_id BIGINT NOT NULL,    -- sharding key: my_user_id
    my_status BOOKING_STATUS NOT NULL,
    -- my_role ROLE_TYPE NOT NULL,  # FIXME: deprecated
    user_id BIGINT NOT NULL,
    "status" BOOKING_STATUS NOT NULL,
    "messages" JSONB DEFAULT '[]'::jsonb,
    previous_reserve JSONB,  -- previous [schedule_id + dtstart],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uidx_reservation_user_dtstart_dtend_schedule_id_user_id
    ON reservations(my_user_id, dtstart, dtend, schedule_id, user_id);
CREATE INDEX idx_reservation_user_my_status_status_dtend
    ON reservations(my_user_id, my_status, "status", dtend);
CREATE INDEX idx_reservation_user_my_status_dtstart_dtend
    ON reservations(my_user_id, my_status, dtstart, dtend);


CREATE TABLE IF NOT EXISTS interests (
    "id" SERIAL PRIMARY KEY,
    category INTEREST_CATEGORY,
    subject_group VARCHAR(40),
    "language" VARCHAR(10),
    "subject" TEXT DEFAULT '',
    "desc" JSONB
);


--以下測試用插入資料
INSERT INTO interests (category, "subject_group", "language", "subject", "desc")
VALUES (
    'INTERESTED_POSITION',          -- category
    'Photography',                  -- subject_group
    'en_US',                        -- language
    'Photography basics and tips',  -- subject
    '{"difficulty": "beginner", "duration": "short"}'::jsonb -- desc (JSONB 格式)
);

INSERT INTO professions (category, "subject_group", "language", "subject", profession_metadata)
VALUES (
    'EXPERTISE',                            -- category
    'Software Development',                 -- subject_group
    'en_US',                                -- language
    'Introduction to Software Engineering', -- subject
    '{"skills": ["programming", "problem-solving"], "experience_required": 3}'::jsonb -- profession_metadata (JSONB 格式)
);
