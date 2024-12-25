from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.mentor.model.mentor_model import (
    TimeSlotDTO,
    MentorScheduleDTO,
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


    async def save_schedules(self, db: AsyncSession, user_id: int, schedule_dto: MentorScheduleDTO) -> MentorScheduleVO:
        try:
            res: MentorScheduleVO = MentorScheduleVO()
            input_timeslots: List[TimeSlotDTO] = schedule_dto.timeslots

            # CHECK: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (這裡需比對資料庫內的時間衝突)
            (min_dtstart, max_dtend) = schedule_dto.min_dtstart_to_max_dtend()
            stored_timeslots: List[TimeSlotDTO] = await self.__schedule_repository \
                .get_schedules_by_time_range(db, user_id, min_dtstart, max_dtend)
            if len(stored_timeslots) > 0:
                merged_timeslots = self.__merge_timeslots(input_timeslots, stored_timeslots)
                MentorScheduleDTO.opverlapping_interval_check(merged_timeslots, schedule_dto.until)

            # save input timeslots only
            saved_timeslots = await self.__schedule_repository.save_schedules(db, input_timeslots)
            res.timeslots = [TimeSlotVO.of(timeslot_dto) for timeslot_dto in saved_timeslots]
            return res

        except Exception as e:
            error_msg = getattr(e, 'msg', str(e)) 
            log.error('save_schedules error: %s', error_msg)
            raise_http_exception(e, msg=error_msg)


    # CHECK: 合併用戶輸入和資料庫內的時間區間
    def __merge_timeslots(self, 
                          input_timeslots: List[TimeSlotDTO], 
                          stored_timeslots: List[TimeSlotDTO]) -> List[TimeSlotDTO]:
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
        merged_timeslots: List[TimeSlotDTO] = []
        if exist_timeslots and new_timeslots:
            exist_timeslots.extend(new_timeslots)
            merged_timeslots = exist_timeslots
        elif new_timeslots:
            merged_timeslots = new_timeslots
        elif exist_timeslots:
            merged_timeslots = exist_timeslots

        return merged_timeslots



    async def delete_schedule(self, db: AsyncSession, user_id: int, schedule_id: int) -> str:
        try:
            deleted_count: int = await self.__schedule_repository.delete_schedule(db, user_id, schedule_id)
            if deleted_count:
                return 'Schedule deleted successfully'
            return 'Schedule not found'

        except Exception as e:
            log.error('delete_schedule error: %s', str(e))
            raise_http_exception(e, msg='Schedule delete failed')
