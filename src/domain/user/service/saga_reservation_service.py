from fastapi.encoders import jsonable_encoder
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.user.model.reservation_model import *
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.config.conf import BATCH
from src.config.exception import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class SagaReservationService:
    def __init__(self, reservation_repository: ReservationRepository):
        self.reservation_repo = reservation_repository
        self.user_repo = None

    async def get_reservations(self, db: AsyncSession,
                               user_id: int, 
                               query_dto: ReservationQueryDTO) -> Optional[ReservationInfoListVO]:
        try:
            res: ReservationInfoListVO = ReservationInfoListVO()
            query_dto.batch += 1
            reservations: List[ReservationInfoVO] = \
                await self.reservation_repo.get_user_reservations(db,
                                                                  user_id,
                                                                  query_dto)
            if len(reservations) < query_dto.batch:
                res.reservations = reservations
            else:
                res.reservations = reservations[:-1]
                res.next_dtend = reservations[-1].dtend
            return res
        except Exception as e:
            log.error('get reservations failed: %s', str(e))
            raise_http_exception(e=e, msg='get reservations failed')


    async def create_sender(self, 
                     db: AsyncSession, 
                     reservation_dto: ReservationDTO
                     ) -> Optional[ReservationVO]:
        try:
            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            await self.reservation_repo.save_all(db, [
                sender,
            ])
            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('[sender] create_reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'sender create_sreservation failed')
            raise_http_exception(e=e, msg=err_msg)


    async def create_participant(self, 
                     db: AsyncSession, 
                     reservation_dto: ReservationDTO
                     ) -> Optional[ReservationVO]:
        try:
            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            await self.reservation_repo.save_all(db, [
                participant,
            ])
            return ReservationVO.from_model(participant)

        except Exception as e:
            log.error('[participant] create_reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'participant create_reservation failed')
            raise_http_exception(e=e, msg=err_msg)



    async def create_sender_new_and_reject_previous(self, 
                                             db: AsyncSession, 
                                             reservation_dto: ReservationDTO
                                             ) -> Optional[ReservationVO]:
        try:
            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            # sender 的上一次預約
            PREV_SENDER_VO: ReservationVO = \
                await self.get_prev_sender_vo(db, reservation_dto)
            prev_sender: Reservation = \
                PREV_SENDER_VO.sender_model(BookingStatus.REJECT, 
                                             PREV_SENDER_VO.id)
            await self.reservation_repo.save_all(db, [
                sender,
                prev_sender,
            ])
            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('[sender] create_sender_new_and_reject_previous reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'sender create_and_cancel reservation failed')
            raise_http_exception(e=e, msg=err_msg)


    async def create_participant_new_and_reject_previous(self, 
                                             db: AsyncSession, 
                                             reservation_dto: ReservationDTO
                                             ) -> Optional[ReservationVO]:
        try:
            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            # sender 的上一次預約
            PREV_SENDER_VO: ReservationVO = \
                await self.get_prev_sender_vo(db, reservation_dto)

            # participant 的上一次預約
            prev_participant_vo: ReservationVO = \
                await self.get_prev_participant_vo(db, PREV_SENDER_VO)
            prev_participant: Reservation = \
                PREV_SENDER_VO.participant_model(BookingStatus.REJECT,
                                                  prev_participant_vo.id)

            # NOTE: 紀錄 participant 的上一次預約!!!!!!!!
            participant.previous_reserve = {
                'reserve_id': prev_participant.id,
            }

            await self.reservation_repo.save_all(db, [
                participant,
                prev_participant,
            ])

            return ReservationVO.from_model(participant)

        except Exception as e:
            log.error('[participant] create_participant_new_and_reject_previous reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'participant create_and_cancel reservation failed')
            raise_http_exception(e=e, msg=err_msg)


    async def update_sender_reservation_status(self, 
                                        db: AsyncSession, 
                                        reserve_id: int, 
                                        update_dto: UpdateReservationDTO
                                        ) -> Optional[ReservationVO]:
        try:
            # 當 ACCEPT 時，檢查時間衝突
            MY_STATUS = update_dto.my_status
            if MY_STATUS == BookingStatus.ACCEPT:
                await self.check_my_accepted_bookings(db, update_dto)

            SENDER_VO: ReservationVO = \
                await self.get_sender_vo_by_id(db, reserve_id, update_dto)
            sender: Reservation = \
                SENDER_VO.sender_model(MY_STATUS, SENDER_VO.id)

            # SENDER_VO 已經取得歷史訊息，可以直接 insert 新訊息，更新狀態
            self.append_new_message(update_dto, sender)
            await self.reservation_repo.save_all(db, [
                sender,
            ])
            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('[sender] updates reservation status failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'sender updates reservation status failed')
            raise_http_exception(e=e, msg=err_msg)


    async def update_participant_reservation_status(self, 
                                        db: AsyncSession, 
                                        reserve_id: int, 
                                        update_dto: UpdateReservationDTO
                                        ) -> Optional[ReservationVO]:
        try:
            MY_STATUS = update_dto.my_status
            SENDER_VO: ReservationVO = \
                await self.get_sender_vo_by_id(db, reserve_id, update_dto)
            participant_vo: ReservationVO = \
                await self.get_participant_vo(db, update_dto)
            participant: Reservation = \
                SENDER_VO.participant_model(MY_STATUS, participant_vo.id)

            # SENDER_VO 已經取得歷史訊息，可以直接 insert 新訊息，更新狀態
            self.append_new_message(update_dto, participant)
            await self.reservation_repo.save_all(db, [
                participant,
            ])

            return ReservationVO.from_model(participant)

        except Exception as e:
            log.error('[participant] updates reservation status failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'participant updates reservation status failed')
            raise_http_exception(e=e, msg=err_msg)


    def append_new_message(self,
                           update_dto: UpdateReservationDTO,
                           reservation: Reservation,
                           ):
        NEW_MESSAGES = update_dto.messages
        if len(NEW_MESSAGES) and \
            isinstance(NEW_MESSAGES[0], Dict) and \
            isinstance(reservation.messages, List):
            reservation.messages.insert(0, NEW_MESSAGES[0])




    '''
    Check my bookings with a status: "ACCEPT"
    '''
    async def check_my_accepted_bookings(self, db: AsyncSession, reservation_dto: ReservationDTO):
        dtstart = reservation_dto.dtstart
        dtend = reservation_dto.dtend
        query: Dict = {
            'my_user_id': reservation_dto.my_user_id,
            'my_status': BookingStatus.ACCEPT,
        }

        # check sender's reservations
        sender_reserve_list: Optional[List[ReservationDTO]] = \
            await self.reservation_repo.find_all(db, query, dtstart, dtend)

        if len(sender_reserve_list) > 0:
            sender_reserve_dict = {idx+1: jsonable_encoder(r) for idx, r in enumerate(sender_reserve_list)}
            raise ClientException(msg='reservation conflict',
                                  data=sender_reserve_dict)

        # checking participant's reservations is not necessary,
        # the default status is 'PENDING'


    async def get_sender_vo_by_id(self, db: AsyncSession, 
                                  reserve_id: int,
                                  update_dto: UpdateReservationDTO) -> Optional[ReservationVO]:
        my_user_id = update_dto.my_user_id
        SENDER_VO: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)
        if not SENDER_VO:
            log.error('sender reservation not found, reserve_id: %s', reserve_id)
            raise ClientException(msg='sender reservation not found')
        
        return SENDER_VO


    async def get_participant_vo(self, db: AsyncSession,
                                 update_dto: UpdateReservationDTO) -> Optional[ReservationVO]:
        query = update_dto.participant_query()
        participant_vo: ReservationVO = \
            await self.reservation_repo.find_one(db, query)
        if not participant_vo:
            log.error('participant reservation not found, query: %s', query)
            raise ClientException(msg='participant reservation not found')

        return participant_vo


    async def get_prev_sender_vo(self, db: AsyncSession, 
                                 reservation_dto: ReservationDTO) -> Optional[ReservationVO]:
        # sender reserve_id 在 reservation_dto.previous_reserve 中
        (reserve_id, my_user_id) = reservation_dto.previous_sender_query_by_id()
        prev_sender_vo: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)

        if not prev_sender_vo:
            log.error('previous sender reservation not found, \
                reserve_id: %s', reserve_id)
            raise ClientException(msg=f'previous sender reservation not found: {reserve_id}')

        return prev_sender_vo


    async def get_prev_participant_vo(self, db: AsyncSession, 
                                      prev_sender_vo: ReservationVO) -> Optional[ReservationVO]:
        p_query = prev_sender_vo.participant_query()
        prev_participant_vo: ReservationVO = \
            await self.reservation_repo.find_one(db, p_query)

        if not prev_participant_vo:
            log.error('previous participant reservation not found, \
                    query: %s', p_query)
            raise ClientException(msg='previous participant reservation not found')

        return prev_participant_vo


class ScaleOutReservationService:
    pass


class CrossRegionReservationService:
    pass
