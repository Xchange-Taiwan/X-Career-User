from profile import Profile

import sqlalchemy.dialects.postgresql
from sqlalchemy import Integer, BigInteger, Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base

from src.config.constant import (
    ProfessionCategory, 
    RoleType, 
    InterestCategory,
    SchedulesType, 
    BookingStatus,
    ExperienceCategory,
)
from src.infra.util.time_util import current_seconds
from src.domain.mentor.enum.mentor_enums import SeniorityLevel
from src.domain.mentor.model.mentor_model import (
    MentorProfileDTO,
    TimeSlotDTO,
)
from src.domain.user.model.common_model import ProfessionVO
from src.domain.user.model.user_model import ProfileDTO

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
    industry = Column(Integer)
    years_of_experience = Column(Integer, default=0)
    region = Column(String, default='')
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
    user_id = Column(BigInteger)
    category = Column(
        ENUM(ExperienceCategory, name='experience_category', create_type=False),
        nullable=False)
    order = Column(Integer, nullable=False)
    desc = Column(JSONB)
    mentor_experiences_metadata = Column(JSONB)


    # profile = relationship("Profile", backref="mentor_experiences")


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

    @staticmethod
    def to_profession_vo(model: 'Profession') -> ProfessionVO:
        return ProfessionVO(**model.__dict__)


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
    exdate = Column(JSON, default=[])               # Use JSONB to store exclusion dates
    created_at = Column(BigInteger, default=current_seconds())
    updated_at = Column(BigInteger, default=current_seconds(), onupdate=current_seconds())
    
    @staticmethod
    def of(dto: TimeSlotDTO):
        if (dto is None):
            return None
        return MentorSchedule(**dto.__dict__)

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
    user_id = Column(BigInteger, nullable=False)
    mentor_schedules_id = Column(Integer, nullable=False)
    start_datetime = Column(Integer)
    end_datetime = Column(Integer)
    my_status = Column(
        ENUM(BookingStatus, name="my_status", create_type=False))
    status = Column(
        ENUM(BookingStatus, name="status", create_type=False))
    role = Column(
        ENUM(RoleType, name="role_type", create_type=False))
    message_from_others = Column(String, default='')
    # profile = relationship("Profile", backref="reservations")
    # mentor_schedule = relationship("MentorSchedule", backref="reservations")


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
