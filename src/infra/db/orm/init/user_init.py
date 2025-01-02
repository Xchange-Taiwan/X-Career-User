from sqlalchemy import Integer, BigInteger, Column, String
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import Optional

from src.config.constant import *

Base = declarative_base()


class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default='')
    job_title = Column(String, default='')
    linkedin_profile = Column(String, default='')
    personal_statement = Column(String, default='')
    about = Column(String, default='')
    company = Column(String, default='')
    seniority_level = Column(
        ENUM(SeniorityLevel, name='seniority_level', create_type=False), nullable=False)

    years_of_experience = Column(Integer, default=0)
    region = Column(String, default='')
    language = Column(String, default='')
    interested_positions = Column(JSONB)
    skills = Column(JSONB)
    topics = Column(JSONB)
    industries = Column(JSONB)
    expertises = Column(JSONB)


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
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    type = Column(
        ENUM(SchedulesType, name="schedule_type", create_type=False))
    year = Column(Integer, default=-1)
    month = Column(Integer, default=-1)
    day_of_month = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    cycle_start_date = Column(Integer)
    cycle_end_date = Column(Integer)
    # profile = relationship("Profile", backref="mentor_schedules")


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
    # my_role = Column( 
    #     ENUM(RoleType, name='role_type', create_type=False))  # FIXME: deprecated
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
