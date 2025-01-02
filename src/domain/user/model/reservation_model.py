import logging as log

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from .user_model import *
from ....config.constant import *
from ....config.conf import BATCH
from ....config.exception import ClientException
from src.infra.db.orm.init.user_init import (
    Reservation,
)

log.basicConfig(filemode='w', level=log.INFO)


class ReservationQueryDTO(BaseModel):
    state: str = Field(None, example=ReservationListState.UPCOMING.value,
                       pattern=f'^({ReservationListState.UPCOMING.value}|{ReservationListState.PENDING.value}|{ReservationListState.HISTORY.value})$')
    batch: int = Field(..., example=BATCH, ge=1)
    next_dtend: Optional[int] = Field(None, example=1735398000)


class UpdateReservationDTO(BaseModel):
    my_user_id: int = 0
    my_status: Optional[BookingStatus] = Field(
        None, example=BookingStatus.PENDING)
    user_id: int = 0
    schedule_id: int = 0
    dtstart: int = 0    # timestamp
    dtend: int = 0      # timestamp
    messages: Optional[List[Dict[str, Any]]] = []

    def participant_query(self) -> Dict:
        return {
            'my_user_id': self.user_id,
            'schedule_id': self.schedule_id,
            'dtstart': self.dtstart,
            'dtend': self.dtend,
            'user_id': self.my_user_id,
        }


'''
讓後端實現「先建立再取消」:
    1. 新建一筆預約，寫上新的 reservation_id (reserve_id);
        並在欄位"previous_reserve" 存儲前一次的[reserve_id]，以便找到同樣的討論串
    2. 將舊的預約設為 cancel
'''


class ReservationDTO(UpdateReservationDTO):
    # sender's previous reservation
    previous_reserve: Optional[Dict[str, Any]] = None

    def sender_model(self, my_status: BookingStatus, id: Optional[int] = None) -> Reservation:
        return Reservation(
            id=id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.my_user_id,
            my_status=my_status,
            # my_role=sender.role,

            user_id=self.user_id,
            status=BookingStatus.PENDING,  # participant's status, in ReservationVO
            messages=self.messages,
            previous_reserve=self.previous_reserve,  # sender's previous reservation
        )

    def participant_model(self, status: BookingStatus, id: Optional[int] = None) -> Reservation:
        return Reservation(
            id=id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.user_id,
            my_status=BookingStatus.PENDING,  # participant's status, in ReservationVO
            # my_role=participant.role,

            user_id=self.my_user_id,
            status=status,
            messages=self.messages,
        )

    def sender_query(self) -> Dict:
        return {
            'my_user_id': self.my_user_id,
            'schedule_id': self.schedule_id,
            'dtstart': self.dtstart,
            'dtend': self.dtend,
            'user_id': self.user_id,
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


class ReservationVO(ReservationDTO):
    id: Optional[int] = None  # id: int 因為沒有經過 await db.refresh()，所以不會有 id
    status: Optional[BookingStatus] = Field(
        None, example=BookingStatus.PENDING)

    class Config:
        from_attributes = True

    @staticmethod
    def from_model(reservation: Reservation) -> 'ReservationVO':
        # sender_role = reservation.my_role
        # participant_role = RoleType.MENTOR if sender_role==RoleType.MENTEE else RoleType.MENTEE
        return ReservationVO(
            id=reservation.id,
            # schedule
            schedule_id=reservation.schedule_id,
            dtstart=reservation.dtstart,
            dtend=reservation.dtend,
            # mine
            my_user_id=reservation.my_user_id,
            my_status=reservation.my_status,
            # antoher side
            user_id=reservation.user_id,
            status=reservation.status,
            # extra info
            previous_reserve=reservation.previous_reserve,
            messages=reservation.messages
        )

    def sender_model(self, my_status: BookingStatus, id: Optional[int] = None) -> Reservation:
        return Reservation(
            id=id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.my_user_id,
            my_status=my_status,
            # my_role=sender.role,

            user_id=self.user_id,
            status=self.status,  # participant's status, in ReservationVO
            messages=self.messages,
            previous_reserve=self.previous_reserve,  # sender's previous reservation
        )

    def participant_model(self, status: BookingStatus, id: Optional[int] = None) -> Reservation:
        return Reservation(
            id=id,
            schedule_id=self.schedule_id,
            dtstart=self.dtstart,
            dtend=self.dtend,

            my_user_id=self.user_id,
            my_status=self.status,  # participant's status, in ReservationVO
            # my_role=participant.role,

            user_id=self.my_user_id,
            status=status,
            messages=self.messages,
        )


class ReservationMessageVO(BaseModel):
    user_id: int = Field(None, example=0)
    # role: Optional[str] = Field(..., example=RoleType.MENTEE.value,
    #                      pattern=f'^({RoleType.MENTOR.value}|{RoleType.MENTEE.value})$')
    content: str = Field(None, example='')


class ReservationInfoVO(BaseModel):
    id: Optional[int] = None
    sender: RUserInfoVO    # sharding key: sneder.user_id
    participant: RUserInfoVO
    schedule_id: int = 0
    dtstart: int = 0    # timestamp
    dtend: int = 0      # timestamp
    previous_reserve: Optional[Dict[str, Any]] = None
    messages: Optional[List[ReservationMessageVO]] = []

    @staticmethod
    def from_sender_model(reservation: Reservation):
        # sender_role = reservation.my_role
        # participant_role = RoleType.MENTOR if sender_role==RoleType.MENTEE else RoleType.MENTEE
        return ReservationInfoVO(
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
                name=reservation.name,
                avatar=reservation.avatar,
                job_title=reservation.job_title,
                years_of_experience=reservation.years_of_experience,
            ),
            schedule_id=reservation.schedule_id,
            dtstart=reservation.dtstart,
            dtend=reservation.dtend,
            previous_reserve=reservation.previous_reserve,
            messages=reservation.messages
        )


class ReservationInfoListVO(BaseModel):
    reservations: Optional[List[ReservationInfoVO]] = []
    next_dtend: Optional[int] = 0
