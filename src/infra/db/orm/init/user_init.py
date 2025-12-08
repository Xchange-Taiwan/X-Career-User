from profile import Profile

import sqlalchemy.dialects.postgresql
from sqlalchemy import Integer, BigInteger, Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import Optional

from src.infra.util.time_util import current_seconds
from src.config.constant import *

Base = declarative_base()


class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    avatar = Column(String(255), default='')
    location = Column(String(100), default='')
    job_title = Column(String(255), default='')
    personal_statement = Column(String, default='')
    about = Column(String, default='')
    company = Column(String(255), default='')
    seniority_level = Column(
        ENUM(SeniorityLevel, name='seniority_level', create_type=False), nullable=False)

    years_of_experience = Column(String(100), default='0')
    industry = Column(String(255))
    interested_positions = Column(JSONB)
    skills = Column(JSONB)
    topics = Column(JSONB)
    expertises = Column(JSONB)
    language = Column(String(10), default='')
    is_mentor = Column(Boolean, default=False)


class MentorExperience(Base):
    __tablename__ = 'mentor_experiences'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    category = Column(
        ENUM(ExperienceCategory, name='experience_category', create_type=False),
        nullable=False)
    order = Column(Integer, nullable=False)
    mentor_experiences_metadata = Column(JSONB)


class Profession(Base):
    __tablename__ = 'professions'
    id = Column(Integer, primary_key=True)
    category = Column(
        ENUM(ProfessionCategory, name="profession_category"),  # Map to PostgreSQL enum
        nullable=False)
    subject_group = Column(String)
    subject = Column(String)
    profession_metadata = Column(JSONB)
    language = Column(String, nullable=False)



class MentorSchedule(Base):
    __tablename__ = 'mentor_schedules'

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
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    role = Column(
        ENUM(RoleType, name="role_type", create_type=False),
        nullable=False)
    message = Column(String)
    # profile = relationship("Profile", backref="canned_messages")


class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, nullable=False)
    dtstart = Column(Integer, nullable=False)
    dtend = Column(Integer, nullable=False)
    my_user_id = Column(BigInteger, nullable=True)  # nullable while updating
    my_status = Column(
        ENUM(BookingStatus, name='booking_status', create_type=False))
    my_role = Column( 
        ENUM(RoleType, name='role_type', create_type=False))
    user_id = Column(BigInteger, nullable=True)     # nullable while updating
    status = Column(
        ENUM(BookingStatus, name='booking_status', create_type=False))
    messages = Column(JSONB, default=[])
    previous_reserve = Column(JSONB, nullable=True) # nullable while updating


class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True)
    category = Column(
        ENUM(InterestCategory, name="interest_category"),  # Map to PostgreSQL enum
        nullable=False)
    subject_group = Column(String)
    subject = Column(String)
    desc = Column(JSONB)
    language = Column(String, nullable=False)
