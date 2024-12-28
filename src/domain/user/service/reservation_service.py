from fastapi.encoders import jsonable_encoder
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.user.model.reservation_model import *
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.config.conf import BATCH
from src.config.exception import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository):
        self.reservation_repo = reservation_repository
        self.user_repo = None

    async def get_reservations(self, db: AsyncSession,
                               query_dto: ReservationQueryDTO) -> Optional[ReservationListVO]:
        try:
            res: ReservationListVO = ReservationListVO()

            query = query_dto.model_dump()
            next_dtstart = query.pop('next_dtstart', None)
            batch = query.pop('batch', BATCH)
            reservations: List[ReservationDTO] = \
                await self.reservation_repo.get_user_reservations(db, query, batch, next_dtstart)

            res.reservations = reservations
            return res
        except Exception as e:
            log.error('get reservations failed: %s', str(e))
            raise_http_exception(e=e, msg='get reservations failed')

    '''
    - reservation_dto 包含兩資訊: sender, participant
    - 對 sender 來說 accept 可能是新建(沒id) 也可以是更新狀態(有id)
    - 若 sender 為新建(沒id)，則檢查時間衝突；若 sender 為更新狀態(有id)，則不需檢查時間衝突
    - 對 participant 來說 accept 可能是新建(沒id) 也可以是更新狀態(有id)
    - 若 participant 為新建(沒id)，不需檢查時間衝突，因為預設狀態為 'PENDING'；
      若 participant 為更新狀態(有id)，也不需檢查時間衝突
    1. sender 沒id? 檢查時間衝突，若有衝突，則拋出異常
    2. 新建/更新 sender 狀態
    3. 新建/更新 participant 狀態
    '''
    async def create(self, db: AsyncSession, reservation_dto: ReservationDTO):
        try:
            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            # TODO: 定義內層的 repository 來處理事務, ReservationRepository當作外層
            # await db.execute(text('BEGIN'))
            await self.reservation_repo.save(db, sender)
            await self.reservation_repo.save(db, participant)
            # await db.commit()

        except Exception as e:
            log.error('create reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'create reservation failed')
            raise_http_exception(e=e, msg=err_msg)


    '''
    - 和 accept 一樣，但多了一步: 拒絕前一次的預約
    - 前一次的預約是根據 reservation_dto 的 previous_reserve 來找到的
    - sender 的 previous_reserve 是前一次的 reserve_id, user_id,...等資訊
    - 根據 previous_reserve 找到 sender 的前一次的預約，並將其狀態設為 'REJECT'
    - participant 那邊的資訊得間接靠 sender 找到:
        - 先透過 previous_reserve 找到對應的 sender 上一次的預約
        - 再透過 sender 上一次的預約找到對應的 participant 上一次的預約
    '''
    async def create_new_and_reject_previous(self, db: AsyncSession, reservation_dto: ReservationDTO):
        try:
            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            # sender 的上一次預約
            PREV_SENDER_VO: ReservationVO = \
                await self.get_prev_sender_vo(db, reservation_dto)
            prev_sender: Reservation = \
                PREV_SENDER_VO.sender_model(BookingStatus.REJECT, 
                                             PREV_SENDER_VO.id)

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

            # 一次完成4個操作: 新建 sender, participant; 更新 sender, participant
            # TODO: 定義內層的 repository 來處理事務, ReservationRepository當作外層
            # await db.execute(text('BEGIN'))
            await self.reservation_repo.save(db, sender)
            await self.reservation_repo.save(db, participant)
            await self.reservation_repo.save(db, prev_sender)
            await self.reservation_repo.save(db, prev_participant)
            # await db.commit()

        except Exception as e:
            log.error('create_and_cancel reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'create_and_cancel reservation failed')
            raise_http_exception(e=e, msg=err_msg)

    '''
    - reject 表示已有資料，只需更新狀態即可；若無資料，則拋出異常
    - 因為 reject 是更新狀態，所以不需要檢查時間衝突
    - reservation_dto 包含兩資訊: sender, participant
    1. 確認 sender 是否存在? 若否，則拋出異常
    2. 確認 participant 是否存在? 若否，則拋出異常
    3. 若 sender 存在，則更新狀態
    4. 若 participant 存在，則更新狀態
    '''

    # FIXME: function 改為 update_reservation_status, 有 id
    async def update_reservation_status(self, db: AsyncSession, reserve_id: int, update_dto: UpdateReservationDTO):
        try:
            SENDER_VO: ReservationVO = await self.get_sender_vo_by_id(db, 
                                                                      reserve_id, 
                                                                      update_dto)

            query = update_dto.participant_query()
            participant_vo: ReservationVO = \
                await self.reservation_repo.find_one(db, query)
            if not participant_vo:
                raise ClientException(msg='participant reservation not found')

            MY_STATUS = update_dto.my_status
            sender: Reservation = \
                SENDER_VO.sender_model(MY_STATUS, SENDER_VO.id)
            participant: Reservation = \
                SENDER_VO.participant_model(MY_STATUS, participant_vo.id)

            # TODO: 定義內層的 repository 來處理事務, ReservationRepository當作外層
            # await db.execute(text('BEGIN'))
            await self.reservation_repo.save(db, sender)
            await self.reservation_repo.save(db, participant)
            # await db.commit()

        except Exception as e:
            log.error('update reservation status failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'update reservation status failed')
            raise_http_exception(e=e, msg=err_msg)

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
            sender_reserve_list = [jsonable_encoder(r) for r in sender_reserve_list]
            raise ClientException(msg='reservation conflict',
                                  data=sender_reserve_list)

        # checking participant's reservations is not necessary,
        # the default status is 'PENDING'


    async def get_sender_vo_by_id(self, db: AsyncSession, 
                                  reserve_id: int,
                                  update_dto: UpdateReservationDTO) -> Optional[ReservationVO]:
        my_user_id = update_dto.my_user_id
        SENDER_VO: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)
        if not SENDER_VO:
            raise ClientException(msg='sender reservation not found')
        
        return SENDER_VO

    async def get_prev_sender_vo(self, db: AsyncSession, 
                                 reservation_dto: ReservationDTO) -> Optional[ReservationVO]:
        # sender reserve_id 在 reservation_dto.previous_reserve 中
        (reserve_id, my_user_id) = reservation_dto.previous_sender_query_by_id()
        prev_sender_vo: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)

        if not prev_sender_vo:
            log.error('previous sender reservation not found, \
                reserve_id: %s', reserve_id)
            raise ClientException(msg='previous sender reservation not found')

        return prev_sender_vo

    async def get_prev_participant_vo(self, db: AsyncSession, 
                                      prev_sender_vo: ReservationVO) -> Optional[ReservationVO]:
        p_query = prev_sender_vo.participant_query()
        prev_participant_vo: ReservationVO = \
            await self.reservation_repo.find_one(db, p_query)

        if not prev_participant_vo:
            log.error('previous participant reservation not found, \
                    query: %s', query)
            raise ClientException(msg='previous participant reservation not found')

        return prev_participant_vo


class ScaleOutReservationService:
    pass


class CrossRegionReservationService:
    pass
