from sqlalchemy import Integer, Column, String, types, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from src.config.constant import ProfessionCategory, RoleType, InterestCategory, SchedulesType, BookingStatus, \
    ExperienceCategory, AccountType
from src.domain.mentor.enum.mentor_enums import SeniorityLevel
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'
    aid = Column(Integer, primary_key=True)
    email1 = Column(String, nullable=False)
    email2 = Column(String)
    pass_hash = Column(String)
    pass_salt = Column(String)
    oauth_id = Column(String)
    refresh_token = Column(String)
    user_id = Column(Integer, unique=True)
    type = Column(type_=types.Enum(AccountType))
    is_active = Column(Boolean)
    region = Column(String)


class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(Integer, ForeignKey('accounts.user_id'), primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default='')
    location = Column(String, default='')
    position = Column(String, default='')
    linkedin_profile = Column(String, default='')
    personal_statement = Column(String, default='')
    about = Column(String, default='')
    company = Column(String, default='')
    seniority_level = Column(PgEnum(SeniorityLevel, name='seniority_level', create_type=False), nullable=False)
    timezone = Column(Integer, default=0)
    experience = Column(Integer, default=0)
    industry = Column(Integer)
    interested_positions = Column(JSONB)
    skills = Column(JSONB)
    topics = Column(JSONB)
    expertises = Column(JSONB)


class MentorExperience(Base):
    __tablename__ = 'mentor_experiences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('profiles.user_id'), nullable=False)
    category = Column(PgEnum(ExperienceCategory, name='experience_category', create_type=False), nullable=False)
    order = Column(Integer, nullable=False)
    desc = Column(JSONB)
    # profile = relationship("Profile", backref="mentor_experiences")


class Profession(Base):
    __tablename__ = 'professions'
    id = Column(Integer, primary_key=True)
    category = Column(type_=types.Enum(ProfessionCategory))
    subject = Column(String)
    profession_metadata = Column(JSONB)


class MentorSchedule(Base):
    __tablename__ = 'mentor_schedules'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('profiles.user_id'), nullable=False)
    type = Column(type_=types.Enum(SchedulesType))
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
    __tablename__ = 'canned_message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('profiles.user_id'), nullable=False)
    role = Column(type_=types.Enum(RoleType), nullable=False)
    message = Column(String)
    # profile = relationship("Profile", backref="canned_message")


class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('profiles.user_id'), nullable=False)
    mentor_schedules_id = Column(Integer, ForeignKey('mentor_schedules.mentor_schedules_id'), nullable=False)
    start_datetime = Column(Integer)
    end_datetime = Column(Integer)
    my_status = Column(name="my_status", type_=types.Enum(BookingStatus))
    status = Column(name="status", type_=types.Enum(BookingStatus))
    role = Column(name="role_type", type_=types.Enum(RoleType))
    message_from_others = Column(String, default='')
    # profile = relationship("Profile", backref="reservations")
    # mentor_schedule = relationship("MentorSchedule", backref="reservations")


class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True)
    category = Column(type_=types.Enum(InterestCategory))
    subject = Column(String)
    desc = Column(JSONB)
