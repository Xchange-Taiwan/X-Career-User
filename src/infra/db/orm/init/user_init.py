from profile import Profile

import sqlalchemy.dialects.postgresql
from sqlalchemy import Integer, Column, String, types
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from src.config.constant import ProfessionCategory, RoleType, InterestCategory, SchedulesType, BookingStatus, \
    ExperienceCategory
from src.domain.mentor.enum.mentor_enums import SeniorityLevel
from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.domain.user.model.common_model import ProfessionVO
from src.domain.user.model.user_model import ProfileDTO

Base = declarative_base()


class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default='')
    location = Column(String, default='')
    job_title = Column(String, default='')
    linkedin_profile = Column(String, default='')
    personal_statement = Column(String, default='')
    about = Column(String, default='')
    company = Column(String, default='')
    seniority_level = Column(
        sqlalchemy.dialects.postgresql.ENUM(SeniorityLevel, name='seniority_level', create_type=False), nullable=False)
    timezone = Column(Integer, default=0)
    experience = Column(Integer, default=0)
    industry = Column(Integer)
    language = Column(String, default='')
    interested_positions = Column(JSONB)
    skills = Column(JSONB)
    topics = Column(JSONB)
    expertises = Column(JSONB)

    # static of function for get user profile
    @staticmethod
    def of(dto: ProfileDTO):
        return Profile(**dto.__dict__)

    @staticmethod
    def of_mentor_profile(dto: MentorProfileDTO):
        return Profile(**dto.__dict__)

    @staticmethod
    def to_dto(model: Profile) -> ProfileDTO:
        return ProfileDTO(**model.__dict__)

    @staticmethod
    def to_mentor_profile_dto(model: Profile) -> MentorProfileDTO:
        if (model is None):
            return None
        return MentorProfileDTO(**model.__dict__)


class MentorExperience(Base):
    __tablename__ = 'mentor_experiences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    category = Column(
        sqlalchemy.dialects.postgresql.ENUM(ExperienceCategory, name='experience_category', create_type=False),
        nullable=False)
    order = Column(Integer, nullable=False)
    desc = Column(JSONB)
    mentor_experiences_metadata = Column(JSONB)


    # profile = relationship("Profile", backref="mentor_experiences")


class Profession(Base):
    __tablename__ = 'professions'
    id = Column(Integer, primary_key=True)
    category = Column(type_=types.Enum(ProfessionCategory))
    subject = Column(String)
    profession_metadata = Column(JSONB)
    language = Column(String, nullable=False)

    @staticmethod
    def to_profession_vo(model: 'Profession') -> ProfessionVO:
        return ProfessionVO(**model.__dict__)

class MentorSchedule(Base):
    __tablename__ = 'mentor_schedules'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
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
    user_id = Column(Integer, nullable=False)
    role = Column(type_=types.Enum(RoleType), nullable=False)
    message = Column(String)
    # profile = relationship("Profile", backref="canned_message")


class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    mentor_schedules_id = Column(Integer, nullable=False)
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
    language = Column(String, nullable=False)
