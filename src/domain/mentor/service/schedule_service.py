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

    async def get_schedule_list(self, db: AsyncSession, filter: Dict = {}, limit: int = BATCH, next_id: Optional[int] = None) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()
            schedule_rows: List[Schedule] = await self.__schedule_repository.get_schedule_list(db, filter, (limit + 1), next_id)
            
            list_size = len(schedule_rows)
            if list_size == 0:
                return res
            
            timeslots: List[TimeSlotVO] = [TimeSlotVO.from_orm(schedule) for schedule in schedule_rows]
            if list_size <= limit:
                res.timeslots = timeslots
            else:
                res.next_id = schedule_rows[-1].id
                res.timeslots = timeslots[:-1]

            return res
        except Exception as e:
            log.error('get_schedule_list error: %s', str(e))
            raise_http_exception(e, msg='Schedule list not found')


    async def save_schedules(self, db: AsyncSession, schedules: List[TimeSlotDTO]) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()
            schedule_rows: List[Schedule] = [Schedule.of(schedule) for schedule in schedules]
            schedule_rows = await self.__schedule_repository.save_schedules(db, schedule_rows)
            res.timeslots = [TimeSlotVO.from_orm(schedule) for schedule in schedule_rows]
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
