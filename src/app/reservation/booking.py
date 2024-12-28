from src.config.constant import BookingStatus
from src.config.exception import ClientException
from src.domain.user.model.reservation_model import (
    ReservationDTO,
)
from src.domain.user.service.reservation_service import ReservationService


class Booking:
    def __init__(self,
                 reservation_service: ReservationService,
                 #  notify_service: NotifyService,
                 ):
        self.reservation_service = reservation_service
        # self.notify_service = notify_service

    # 聚合根 => 原子性的完成
    async def accept(self, db, reservation_dto: ReservationDTO):            
        if reservation_dto.previous_reserve:
            await self.reservation_service.accept_new_and_reject_previous(db, reservation_dto)
        else:
            await self.reservation_service.accept(db, reservation_dto)

        # TODO: notify participant
        # notify_service.notify_participant(reservation_dto)

    # 聚合根 => 原子性的完成
    async def reject(self, db, reservation_dto: ReservationDTO):
        await self.reservation_service.reject(db, reservation_dto)

        # TODO: notify participant
        # notify_service.notify_participant(reservation_dto)


'''
ScaleOutBooking 用來處理跨 DB 的預約建立、更新狀態的操作:
    - SAGA Pattern
'''


class ScaleOutBooking:
    def __init__(self, remote_reservation_service):
        self.reservation_service = remote_reservation_service

    async def accept(self, db_list, reservation_dto: ReservationDTO):

        # sender
        db = db_list.next_db  # sharding by my_user_id
        # TODO: check date conflict with sender
        await self.reservation_service.accept(db, reservation_dto)

        # participant
        db = db_list.next_db  # sharding by user_id
        await self.reservation_service.accept(db, reservation_dto)

        # TODO: notify participant
        # notify_service.notify_participant(reservation_dto)

    async def reject(self, db_list, reservation_dto: ReservationDTO):

        # sender
        db = db_list.next_db  # sharding by my_user_id
        # TODO: check date conflict with sender
        await self.reservation_service.reject(db, reservation_dto)
        # participant
        # db = db.next_db(sharding by user_id)
        db = db_list.next_db  # sharding by user_id
        await self.reservation_service.reject(db, reservation_dto)

        # TODO: notify participant
        # notify_service.notify_participant(reservation_dto)


'''
CrossRegionBooking 用來處理跨地區的預約建立、更新狀態的操作
'''


class CrossRegionBooking:
    pass
