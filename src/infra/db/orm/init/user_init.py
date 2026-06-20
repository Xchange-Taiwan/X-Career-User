from sqlalchemy import (
    Integer,
    BigInteger,
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import Optional

from src.infra.util.time_util import current_seconds
from src.config.constant import *

Base = declarative_base()


class Profile(Base):
    __tablename__ = 'profiles'
    __table_args__ = (
        CheckConstraint(
            "seniority_level IN "
            "('NO REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER')",
            name='ck_profiles_seniority_level',
        ),
    )

    user_id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    avatar = Column(Text, default='')
    location = Column(Text, default='')
    job_title = Column(Text, default='')
    linkedin_profile = Column(Text, default='')
    personal_statement = Column(String, default='')
    about = Column(String, default='')
    company = Column(Text, default='')
    seniority_level = Column(String(20))

    years_of_experience = Column(String, default='0')
    industry = Column(Text)
    language = Column(String(10), default='')
    is_mentor = Column(Boolean, default=False)
    # Mentor-side tag selections, stored as flat subject_group arrays. Kind
    # comes from the tags catalog (a JOIN at read time buckets these into
    # want_position / want_skill / want_topic / have_skill / have_topic).
    want_tags = Column(ARRAY(String), nullable=False, server_default='{}')
    have_tags = Column(ARRAY(String), nullable=False, server_default='{}')
    # Mentor experiences live inline as JSONB[]. Each element is an
    # ExperienceVO dict (category / order / mentor_experiences_metadata).
    # Replaces the former mentor_experiences table — every PUT overwrites
    # the column wholesale, so there is no per-row diff to manage.
    experiences = Column(JSONB, nullable=False, server_default='[]')


class MentorSchedule(Base):
    __tablename__ = 'mentor_schedules'
    __table_args__ = (
        CheckConstraint(
            "dt_type IN ('ALLOW', 'FORBIDDEN')",
            name='ck_mentor_schedules_dt_type',
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)    # User ID
    dt_type = Column(String(20), nullable=False) # Event type
    dt_year = Column(Integer, nullable=False, index=True)       # Year
    dt_month = Column(Integer, nullable=False, index=True)      # Month
    dtstart = Column(BigInteger, nullable=False, index=True)    # Start time
    dtend = Column(BigInteger, nullable=False, index=True)      # End time
    timezone = Column(String(50), nullable=False)   # Timezone
    rrule = Column(Text, nullable=True)             # Repeat event rules
    exdate = Column(JSONB, default=[])               # Use JSONB to store exclusion dates
    created_at = Column(BigInteger, default=current_seconds())
    updated_at = Column(BigInteger, default=current_seconds(), onupdate=current_seconds())


    def __repr__(self):
        return f'<MentorSchedules(id={self.id}, \
            user_id={self.user_id}, \
            dt_type={self.dt_type}, \
            dt_year={self.dt_year}, \
            dt_month={self.dt_month}, \
            dtstart={self.dtstart}, \
            dtend={self.dtend}, \
            rrule={self.rrule}, \
            exdate={self.exdate})>'


class CannedMessage(Base):
    __tablename__ = 'canned_messages'
    __table_args__ = (
        CheckConstraint(
            "role IN ('MENTOR', 'MENTEE')",
            name='ck_canned_messages_role',
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    role = Column(String(20), nullable=False)
    message = Column(String)
    # profile = relationship("Profile", backref="canned_messages")


class Reservation(Base):
    __tablename__ = 'reservations'
    __table_args__ = (
        CheckConstraint(
            "my_status IN ('ACCEPT', 'PENDING', 'REJECT')",
            name='ck_reservations_my_status',
        ),
        CheckConstraint(
            "my_role IS NULL OR my_role IN ('MENTOR', 'MENTEE')",
            name='ck_reservations_my_role',
        ),
        CheckConstraint(
            "status IN ('ACCEPT', 'PENDING', 'REJECT')",
            name='ck_reservations_status',
        ),
    )

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, nullable=False)
    dtstart = Column(Integer, nullable=False)
    dtend = Column(Integer, nullable=False)
    my_user_id = Column(BigInteger, nullable=True)  # nullable while updating
    my_status = Column(String(20), nullable=False)
    my_role = Column(String(20))
    user_id = Column(BigInteger, nullable=True)     # nullable while updating
    status = Column(String(20), nullable=False)
    messages = Column(JSONB, default=[])
    previous_reserve = Column(JSONB, nullable=True) # nullable while updating


class Activity(Base):
    __tablename__ = 'activities'
    __table_args__ = (
        CheckConstraint(
            "service IN ('GOOGLE')",
            name='ck_activities_service',
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'CANCELLED')",
            name='ck_activities_status',
        ),
    )

    id = Column(String(255), primary_key=True, nullable=False)
    mentor_reservation_id = Column(Integer, nullable=False, index=True)
    mentee_reservation_id = Column(Integer, nullable=False, index=True)
    service = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f'<Activity(id={self.id}, \
            mentor_reservation_id={self.mentor_reservation_id}, \
            mentee_reservation_id={self.mentee_reservation_id}, \
            service={self.service}, \
            status={self.status})>'


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(BigInteger, primary_key=True)
    kind = Column(String(20), nullable=False)
    subject_group = Column(String(40))
    language = Column(String(10))
    subject = Column(Text, nullable=False, default='')
    desc = Column(JSONB)
    # parent_subject_group IS NULL ⇔ group row (catalog scaffolding);
    # NOT NULL ⇔ leaf. _validate_leaves enforces this as a write-time
    # invariant so orphan leaves can't accumulate.
    parent_subject_group = Column(String(40), nullable=True, index=True)
