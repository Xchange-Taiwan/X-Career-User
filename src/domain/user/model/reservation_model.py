
from sqlalchemy import Column, Integer, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base

from .user_model import *
from ...mentor.enum.mentor_enums import ScheduleType
from ....config.conf import *
from ....config.constant import *
import logging as log
from sqlalchemy import types
log.basicConfig(filemode='w', level=log.INFO)

Base = declarative_base()





class MentorSchedules(Base):
    __tablename__ = 'mentor_schedules'

    mentor_schedules_id = Column(Integer, primary_key=True)
    type = Column(types.Enum(ScheduleType), default=ScheduleType.ALLOW)
    year = Column(Integer, default=-1)
    month = Column(Integer, default=-1)
    day_of_month = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    cycle_start_date = Column(BigInteger)
    cycle_end_date = Column(BigInteger)


class Reservations(Base):
    __tablename__ = 'reservations'

    reservations_id = Column(Integer, primary_key=True)
    mentor_id = Column(Integer, nullable=False)
    mentee_id = Column(Integer, nullable=False)
    start_datetime = Column(BigInteger)
    end_datetime = Column(BigInteger)
    my_status = Column(types.Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    status = Column(types.Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    role = Column(types.Enum(RoleType))
    message_from_others = Column(Text, default='')

class UserDTO(BaseModel):
    user_id: int
    role: RoleType


class ReservationDTO(BaseModel):
    schedule_id: int
    participant: UserDTO
    my_status: BookingStatus
    start_datetime: int
    end_datetime: int
    message: Optional[str]


class AsyncUserDataVO(UserDTO):
    name: Optional[str]
    avatar: Optional[str]
    position: Optional[str]
    company: Optional[str]
    industry: Optional[ProfessionVO]
    status: BookingStatus


class ReservationVO(BaseModel):
    id: int
    schedule_id: int
    participant: AsyncUserDataVO
    my_status: BookingStatus
    start_datetime: int
    end_datetime: int
    message: Optional[str]


class ReservationListVO(BaseModel):
    reservations: List[ReservationVO]
    next_id: Optional[int]


# class MentorSchedulesDTO(BaseModel):
#     mentor_schedules_id: int
#     type: str
#     year: int = -1
#     month: int = -1
#     day_of_month: int
#     day_of_week: int
#     start_time: int
#     end_time: int
#     cycle_start_date: Optional[int] = None
#     cycle_end_date: Optional[int] = None
#
#
# class ReservationsDTO(BaseModel):
#     reservations_id: int
#     mentor_id: int
#     mentee_id: int
#     start_datetime: Optional[int] = None
#     end_datetime: Optional[int] = None
#     my_status: str = 'pending'
#     status: str = 'pending'
#     role: Optional[str] = None
#     message_from_others: Optional[str] = ''
