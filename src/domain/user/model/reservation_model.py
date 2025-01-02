from .common_model import ProfessionVO
from .user_model import *
from ....config.constant import *
import logging as log


log.basicConfig(filemode='w', level=log.INFO)


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

# class MentorScheduleDTO(BaseModel):
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
# class ReservationDTO(BaseModel):
#     reservations_id: int
#     mentor_id: int
#     mentee_id: int
#     start_datetime: Optional[int] = None
#     end_datetime: Optional[int] = None
#     my_status: str = 'pending'
#     status: str = 'pending'
#     role: Optional[str] = None
#     message_from_others: Optional[str] = ''
