from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.mentor.model.mentor_model import (
    TimeSlotDTO,
    TimeSlotVO,
    MentorScheduleVO,
)
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.infra.db.orm.init.user_init import MentorSchedule as Schedule
from src.config.exception import (
    raise_http_exception,
    ClientException,
)


import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ScheduleService:
    def __init__(self, schedule_repository: ScheduleRepository):
        self.__schedule_repository: ScheduleRepository = schedule_repository

    async def get_schedule_list(self, db: AsyncSession, filter: Dict = {}, limit: Optional[int] = None, next_dtstart: Optional[int] = None) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()
            limit = (limit + 1) if limit else None
            timeslot_dtos: List[Optional[TimeSlotDTO]] = await self.__schedule_repository.get_schedule_list(db, filter, limit, next_dtstart)

            list_size = len(timeslot_dtos)
            if list_size == 0:
                return res

            timeslot_vos: List[TimeSlotVO] = [TimeSlotVO.of(timeslot_dto) for timeslot_dto in timeslot_dtos]
            if not limit or list_size < limit:
                res.timeslots = timeslot_vos
            else:
                res.next_dtstart = timeslot_vos[-1].dtstart
                res.timeslots = timeslot_vos[:-1]

            return res
        except Exception as e:
            log.error('get_schedule_list error: %s', str(e))
            raise_http_exception(e, msg='Schedule list not found')


    async def save_schedules(self, db: AsyncSession, user_id: int, timeslot_dtos: List[TimeSlotDTO]) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()

            # CHECK: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (這裡需比對資料庫內的時間衝突)
            (min_dtstart, max_dtend) = TimeSlotDTO.min_dtstart_and_max_dtend(timeslot_dtos)
            stored_timeslot_dtos: List[TimeSlotDTO] = await self.__schedule_repository \
                .get_schedules_by_time_range(db, user_id, min_dtstart, max_dtend)
            if len(stored_timeslot_dtos) > 0:
                self.__datetime_conflict_check(timeslot_dtos, stored_timeslot_dtos)


            timeslot_dtos = await self.__schedule_repository.save_schedules(db, timeslot_dtos)
            res.timeslots = [TimeSlotVO.of(timeslot_dto) for timeslot_dto in timeslot_dtos]
            return res
        except Exception as e:
            log.error('save_schedules error: %s', str(e))
            raise_http_exception(e, msg='Schedule save failed' if not e.msg else e.msg)


    # CHECK: 檢查是否有時間重疊
    def __datetime_conflict_check(self, input_timeslots: List[TimeSlotDTO], stored_timeslots: List[TimeSlotDTO]):
        # 1) stored in database
        stored_timeslots_dict: Dict[int, TimeSlotDTO] = {timeslot.id: timeslot for timeslot in stored_timeslots}
        # 2) user inputs timeslots with id
        update_timeslot_dict: Dict[int, TimeSlotDTO]  = {timeslot.id: timeslot for timeslot in input_timeslots if timeslot.id}
        # 3) timeslots with id: merge 1) and 2)
        stored_timeslots_dict.update(update_timeslot_dict)
        exist_timeslots = [exist_timeslot for exist_timeslot in stored_timeslots_dict.values()]

        # 4) user inputs timeslots without id
        new_timeslots: List[TimeSlotDTO] = [input_timeslot for input_timeslot in input_timeslots if not input_timeslot.id]

        # merge 3) and 4)
        timeslots: List[TimeSlotDTO] = []
        if exist_timeslots and new_timeslots:
            exist_timeslots.extend(new_timeslots)
            timeslots = exist_timeslots
        elif new_timeslots:
            timeslots = new_timeslots
        elif exist_timeslots:
            timeslots = exist_timeslots


        # Check Conflicts by Greedy Algorithm
        TimeSlotDTO.datetime_conflict_check(timeslots)



    async def delete_schedule(self, db: AsyncSession, user_id: int, schedule_id: int) -> str:
        try:
            deleted_count: int = await self.__schedule_repository.delete_schedule(db, user_id, schedule_id)
            if deleted_count:
                return 'Schedule deleted successfully'
            return 'Schedule not found'

        except Exception as e:
            log.error('delete_schedule error: %s', str(e))
            raise_http_exception(e, msg='Schedule delete failed')
