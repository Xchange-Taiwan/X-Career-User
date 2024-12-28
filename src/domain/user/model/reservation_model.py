import logging as log

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from .common_model import ProfessionVO
from .user_model import *
from ....config.constant import *
from ....config.conf import BATCH
from ....config.exception import ClientException
from src.infra.db.orm.init.user_init import (
    Reservation,
)

log.basicConfig(filemode='w', level=log.INFO)


# class RUserDTO(BaseModel):
#     user_id: Optional[int] = Field(None, example=0)
#     # role: Optional[str] = Field(None, example=RoleType.MENTEE.value,
#     #                      pattern=f'^({RoleType.MENTOR.value}|{RoleType.MENTEE.value})$')
#     # status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
#     #                      pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')


# class ReservationStatusDTO(BaseModel):
#     id: int = 0
#     sender: RUserDTO
#     message: Optional[str] = ''


'''
讓後端實現「先建立再取消」:
    1. 新建一筆預約，寫上新的 schedule_id, dtstart;
        並在欄位"previous_reserve" 存儲前一次的[schedule_id, dtstart]，以便找到同樣的討論串
    2. 將舊的預約設為 cancel
'''


class ReservationDTO(BaseModel):
    id: Optional[int] = None
    # sender: RUserDTO    # sharding key: sneder.user_id
    my_user_id: int = 0
    my_status: Optional[BookingStatus] = Field(None, example=BookingStatus.PENDING)
    # my_status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
    #                         pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')
    # id2: Optional[int] = None
    # participant: RUserDTO
    user_id: int = 0
    status: Optional[BookingStatus] = Field(None, example=BookingStatus.PENDING)
    # status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
    #                         pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')
    
    schedule_id: int = 0
    dtstart: int = 0    # timestamp
    dtend: int = 0      # timestamp
    messages: Optional[List] = []
    previous_reserve: Optional[Dict[str, Any]] = None # sender's previous reservation

    # class Config:
    #     from_attributes = True

    @staticmethod
    def from_model(reservation: Reservation):
        # sender_role = reservation.my_role
        # participant_role = RoleType.MENTOR if sender_role==RoleType.MENTEE else RoleType.MENTEE
        return ReservationDTO(
            id=reservation.id,
            schedule_id=reservation.schedule_id,
            dtstart=reservation.dtstart,
            dtend=reservation.dtend,
            
            my_user_id=reservation.my_user_id,
            my_status=reservation.my_status,
            # sender=RUserDTO(
            #         user_id=reservation.my_user_id,
            #         # role=sender_role,
            #         status=reservation.my_status,
            #     ),
            user_id=reservation.user_id,
            status=reservation.status,
            # participant=RUserDTO(
            #         user_id=reservation.user_id,
            #         # role=participant_role,
            #         status=reservation.status,
            #     ),
            
            previous_reserve=reservation.previous_reserve,
            messages=reservation.messages
        )
    
    def sender_model(self, my_status: BookingStatus) -> Reservation:
        return Reservation(
            id=self.id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.my_user_id,
            my_status=my_status,
            # my_role=sender.role,

            user_id=self.user_id,
            status=self.status,
            messages=self.messages,
            previous_reserve=self.previous_reserve, # sender's previous reservation
        )
    
    def participant_model(self, status: BookingStatus, id: Optional[int] = None) -> Reservation:
        return Reservation(
            id=id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.user_id,
            my_status=self.status,
            # my_role=participant.role,

            user_id=self.my_user_id,
            status=status,
            messages=self.messages,
        )

    def participant_query(self) -> Dict:
        return {
            'my_user_id': self.user_id,
            'schedule_id': self.schedule_id,
            'dtstart': self.dtstart,
            'dtend': self.dtend,
            'user_id': self.my_user_id,
        }

    def previous_sender_query_by_id(self) -> Tuple[int, int]:
        if not self.previous_reserve or not 'reserve_id' in self.previous_reserve:
            raise ClientException(msg='previous reserve_id not found')

        return (
            self.previous_reserve.get('reserve_id'),
            self.my_user_id,
        )

    @staticmethod
    def overlapping_interval_check(reservations: List['ReservationDTO']):
        reservations.sort(key=lambda reserve: reserve.dtend)
        conflict_records: Dict = {}

        conflicts = 0
        prev_reserve = reservations[0]
        for reserve in reservations[1:]:
            if prev_reserve.dtend > reserve.dtstart:
                conflicts += 1
                conflict_records.update({
                    conflicts: jsonable_encoder(prev_reserve)
                })
            else:
                prev_reserve = reserve

        if conflicts > 0:
            be = 'is' if conflicts == 1 else 'are'
            noun = 'conflict' if conflicts == 1 else 'conflicts'
            raise ClientException(msg=f'There {be} {conflicts} {noun}',
                                  data={'conflicts': conflict_records})




# class ReservationMessageVO(BaseModel):
#     id: Optional[int]
#     # msg's sharding key: schedule_id + dtstart(only YYmmdd?) for both sides
#     # 如何改預約時段?? 新建立預約後再 cancel 舊的。也能保證找到同個時段的所有 message。
#     schedule_id: int
#     dtstart: int
#     message: str


class RUserInfoVO(BaseModel):
    user_id: Optional[int] = Field(None, example=0)
    # role: Optional[str] = Field(None, example=RoleType.MENTEE.value,
    #                      pattern=f'^({RoleType.MENTOR.value}|{RoleType.MENTEE.value})$')
    status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
                         pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    job_title: Optional[str] = ''
    years_of_experience: Optional[int] = 0


# class AsyncUserDataVO(RUserDTO):
#     name: Optional[str]
#     avatar: Optional[str]
#     position: Optional[str]
#     company: Optional[str]
#     industry: Optional[ProfessionVO]
#     status: BookingStatus


# class ReservationVO(BaseModel):
#     # reservation sharding key: user_id
#     id: int
#     # user_id: int # 同樣的 user_id 在 VO 可省略不顯示
#     schedule_id: int
#     participant: AsyncUserDataVO
#     my_status: BookingStatus
#     dtstart: int  # timestamp
#     dtend: int   # timestamp
#     # msg's sharding key: schedule_id + dtstart(only YYmmdd?) for both sides
#     # NOTE: 需要一個獨立的 table 來存儲 message_log? 新建立和取消預約的 message 共兩筆，需視為同樣的討論串
#     # message: Optional[str]
#     message: Optional[ReservationMessageVO]

#     # NOTE: 在 UI 上，若變更預約 又不想先建立再取消，則
#     # 需在此處新增一個欄位來存儲前一次的[schedule_id, dtstart]，以便找到同樣的討論串
#     '''
#     讓後端實現「先建立再取消」:
#         1. 新建一筆預約，寫上新的 schedule_id, dtstart;
#             並在欄位"previous_reserve" 存儲前一次的[schedule_id, dtstart]，以便找到同樣的討論串
#         2. 將舊的預約設為 cancel
#     '''
#     previous_reserve: Optional[Dict[str, Any]]


class ReservationQueryDTO(BaseModel):
    user_id: int
    state: ReservationListState = Field(None, example=ReservationListState.UPCOMING.value,
        pattern=f'^({ReservationListState.UPCOMING.value}|\
                {ReservationListState.PENDING.value}|\
                {ReservationListState.HISTORY.value})$')
    batch: int = BATCH
    next_dtstart: Optional[int] = None
    
    # my_user_id: int
    # my_status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
    #                         pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')
    # status: Optional[str] = Field(None, example=BookingStatus.PENDING.value,
    #                         pattern=f'^({BookingStatus.ACCEPT.value}|{BookingStatus.REJECT.value}|{BookingStatus.PENDING.value})$')


    def query(self) -> Dict:
        if self.state == ReservationListState.UPCOMING:
            return {
                'my_user_id': self.user_id,
                'my_status': BookingStatus.ACCEPT.value,
                'status': BookingStatus.ACCEPT.value,
                'dtstart': self.next_dtstart
            }
        if self.state == ReservationListState.PENDING:
            return {
                'my_user_id': self.user_id,
                'my_status': BookingStatus.PENDING.value,
                # 'status': BookingStatus.PENDING.value
            }

        # if self.state == ReservationListState.HISTORY:
        return {
            'my_user_id': self.user_id,
            'my_status': BookingStatus.REJECT.value,
            # 'status': BookingStatus.REJECT.value,
            'dtstart': self.next_dtstart
        }



class ReservationMessageVO(BaseModel):
    user_id: int = Field(None, example=0)
    role: Optional[str] = Field(..., example=RoleType.MENTEE.value,
                         pattern=f'^({RoleType.MENTOR.value}|{RoleType.MENTEE.value})$')
    message: str = Field(None, example='')


class ReservationVO(BaseModel):
    id: Optional[int] = None
    sender: RUserInfoVO    # sharding key: sneder.user_id
    # id2: Optional[int] = None
    participant: RUserInfoVO
    schedule_id: int = 0
    dtstart: int = 0    # timestamp
    dtend: int = 0      # timestamp
    previous_reserve: Optional[Dict[str, Any]] = None
    messages: Optional[List[ReservationMessageVO]] = ''


    @staticmethod
    def from_sender_model(reservation: Reservation):
        # sender_role = reservation.my_role
        # participant_role = RoleType.MENTOR if sender_role==RoleType.MENTEE else RoleType.MENTEE
        return ReservationVO(
            id=reservation.id,
            sender=RUserInfoVO(
                    user_id=reservation.my_user_id,
                    # role=sender_role,
                    status=reservation.my_status,
                ),
            participant=RUserInfoVO(
                    user_id=reservation.user_id,
                    # role=participant_role,
                    status=reservation.status,
                ),
            schedule_id=reservation.schedule_id,
            dtstart=reservation.dtstart,
            dtend=reservation.dtend,
            previous_reserve=reservation.previous_reserve,
            message=reservation.messages
        )

class ReservationListVO(BaseModel):
    reservations: List[ReservationVO]
    next_dtstart: Optional[int]

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
