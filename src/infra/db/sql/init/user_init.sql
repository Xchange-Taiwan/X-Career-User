CREATE TYPE SENIORITY_LEVEL AS ENUM('NO_REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER');
CREATE TYPE INTEREST_CATEGORY AS ENUM('INTERESTED_POSITION', 'SKILL', 'TOPIC');
CREATE TYPE PROFESSION_CATEGORY AS ENUM('EXPERTISE', 'INDUSTRY');
CREATE TYPE EXPERIENCE_CATEGORY AS ENUM('WORK', 'EDUCATION', 'LINK');
CREATE TYPE SCHEDULE_TYPE AS ENUM('ALLOW', 'FORBIDDEN');
CREATE TYPE BOOKING_STATUS AS ENUM('ACCEPT', 'PENDING', 'REJECT');
CREATE TYPE ROLE_TYPE AS ENUM('MENTOR', 'MENTEE');
CREATE TYPE industry_category AS ENUM (
    'SOFTWARE',
    'HARDWARE',
    'SERVICE',
    'FINANCE',
    'OTHER'
);
CREATE TYPE account_type AS ENUM('XC', 'GOOGLE', 'LINKEDIN');


CREATE TABLE accounts (
    aid SERIAL PRIMARY KEY,
    email1 TEXT NOT NULL,
    email2 TEXT,
    pass_hash TEXT,
    pass_salt TEXT,
    oauth_id TEXT,
    refresh_token TEXT,
    user_id INTEGER UNIQUE,
    type account_type,
    is_active BOOL,
    region TEXT
);
CREATE TABLE profiles (
    user_id SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    avatar TEXT DEFAULT '',
    "region" TEXT DEFAULT '',
    "job_title" TEXT DEFAULT '',
    linkedin_profile TEXT DEFAULT '',
    personal_statement TEXT DEFAULT '',
    about TEXT DEFAULT '',
    company TEXT DEFAULT '',
    seniority_level SENIORITY_LEVEL,
    years_of_experience INT DEFAULT 0,
	industry INT,
    interested_positions JSONB,
    skills JSONB,
    topics JSONB,
    expertises JSONB,
    "language" varchar(10)
    --,CONSTRAINT fk_profile_user_id FOREIGN KEY (user_id) REFERENCES accounts(user_id)
);


CREATE TABLE mentor_experiences (
    "id" SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    category EXPERIENCE_CATEGORY NOT NULL,
    "order" INT NOT NULL,
    'desc' JSONB,
    mentor_experiences_metadata JSONB
    --,CONSTRAINT fk_profile_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);


CREATE TABLE professions (
    "id" SERIAL PRIMARY KEY,
    category PROFESSION_CATEGORY ,
    "language" varchar(10),
    subject TEXT DEFAULT '',
    profession_metadata JSONB
);

CREATE TABLE mentor_schedules (
    "id" SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    "type" SCHEDULE_TYPE DEFAULT 'ALLOW',
    "year" INT DEFAULT -1,
    "month" INT DEFAULT -1,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    start_time INT NOT NULL,
    end_time INT NOT NULL,
    cycle_start_date BIGINT,
    cycle_end_date BIGINT
    --,CONSTRAINT fk_profile_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);

CREATE INDEX mentor_schedule_index ON mentor_schedules("year", "month", day_of_month, day_of_week, start_time, end_time);

CREATE TABLE canned_message (
    "id" SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    "role" ROLE_TYPE NOT NULL,
    MESSAGE TEXT
    --,CONSTRAINT fk_profiles_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id)
);

CREATE TABLE reservations (
    "id" SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mentor_schedules_id INT NOT NULL,
    start_datetime BIGINT,
    end_datetime BIGINT,
    my_status BOOKING_STATUS ,
    status BOOKING_STATUS,
    "role" ROLE_TYPE,
    message_from_others TEXT DEFAULT ''
    --,CONSTRAINT fk_profiles_user_id FOREIGN KEY (user_id) REFERENCES profiles(user_id),
    --CONSTRAINT fk_mentor_schedules_id FOREIGN KEY (mentor_schedules_id) REFERENCES mentor_schedules("id")
);

CREATE INDEX reservations_index ON reservations(user_id, start_datetime, end_datetime);

CREATE TABLE interests (
    id SERIAL,
    "language" VARCHAR(10),
    category INTEREST_CATEGORY,
    subject TEXT,
    "desc" JSONB,
    PRIMARY KEY (id, language)
);


--以下測試用插入資料
INSERT INTO public.interests
("id", "language", category, subject, "desc")
values(1, 'ENG', 'INTERESTED_POSITION', 'TEST', '{}');

INSERT INTO public.professions
("id", category, subject, "professions_metadata")
values(1, 'EXPERTISE', 'TEST', '{}');