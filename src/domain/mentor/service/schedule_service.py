from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.conf import BATCH
from src.domain.mentor.model.mentor_model import (
    TimeSlotDTO,
    TimeSlotVO,
    MentorScheduleVO,
)
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.infra.db.orm.init.user_init import MentorSchedule as Schedule
from src.config.exception import raise_http_exception


import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ScheduleService:
    def __init__(self, schedule_repository: ScheduleRepository):
        self.__schedule_repository: ScheduleRepository = schedule_repository

    async def get_schedule_list(self, db: AsyncSession, filter: Dict = {}, limit: int = BATCH, next_dtstart: Optional[int] = None) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()
            timeslot_dtos: List[Optional[TimeSlotDTO]] = await self.__schedule_repository.get_schedule_list(db, filter, (limit + 1), next_dtstart)

            list_size = len(timeslot_dtos)
            if list_size == 0:
                return res

            timeslot_vos: List[TimeSlotVO] = [TimeSlotVO.of(timeslot_dto) for timeslot_dto in timeslot_dtos]
            if list_size <= limit:
                res.timeslots = timeslot_vos
            else:
                res.next_dtstart = timeslot_vos[-1].dtstart
                res.timeslots = timeslot_vos[:-1]

            return res
        except Exception as e:
            log.error('get_schedule_list error: %s', str(e))
            raise_http_exception(e, msg='Schedule list not found')


    async def save_schedules(self, db: AsyncSession, timeslot_dtos: List[TimeSlotDTO]) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()

            # TODO: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (等有人開始用 反饋了再優化)
            # 這裡需比對資料庫內的時間衝突
            timeslot_dtos = await self.__schedule_repository.save_schedules(db, timeslot_dtos)
            res.timeslots = [TimeSlotVO.of(timeslot_dto) for timeslot_dto in timeslot_dtos]
            return res
        except Exception as e:
            log.error('save_schedules error: %s', str(e))
            raise_http_exception(e, msg='Schedule save failed')


    async def delete_schedule(self, db: AsyncSession, user_id: int, schedule_id: int) -> str:
        try:
            deleted_count: int = await self.__schedule_repository.delete_schedule(db, user_id, schedule_id)
            if deleted_count:
                return 'Schedule deleted successfully'
            return 'Schedule not found'

        except Exception as e:
            log.error('delete_schedule error: %s', str(e))
            raise_http_exception(e, msg='Schedule delete failed')
