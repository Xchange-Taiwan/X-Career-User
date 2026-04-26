import logging
from typing import List, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import (
    raise_http_exception,
)
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.domain.mentor.model.mentor_model import (
    TimeSlotDTO,
    MentorScheduleDTO,
    TimeSlotVO,
    MentorScheduleVO,
    MentorScheduleQueryVO,
    MentorScheduleSegmentVO,
)
from src.infra.util.time_util import month_range_ts

log = logging.getLogger(__name__)


class ScheduleService:
    def __init__(self, schedule_repository: ScheduleRepository):
        self.__schedule_repository: ScheduleRepository = schedule_repository

    async def get_schedule_list(
        self,
        db: AsyncSession,
        user_id: int,
        dt_year: int,
        dt_month: int,
        limit: Optional[int] = None,
        next_dtstart: Optional[int] = None,
    ) -> MentorScheduleQueryVO:
        # 回傳該 mentor 於指定年月的三類時段：
        # - ALLOW/FORBIDDEN: 原始 schedule（包含 rrule/exdate），不在後端展開
        # - BOOKED/PENDING: mentor reservation 依 my_status 對應的區間
        # rrule 解析與可用時段推導改由前端處理
        try:
            window_start, window_end = month_range_ts(dt_year, dt_month)

            schedules = await self.__schedule_repository.get_month_schedules_all_types(
                db, user_id, dt_year, dt_month)
            reservations = await self.__schedule_repository.get_schedule_related_reservations_of_mentor(
                db, user_id, window_start, window_end)

            segments: List[MentorScheduleSegmentVO] = [
                MentorScheduleSegmentVO.timeslot_to_segment(timeslot)
                for timeslot in schedules
            ]
            segments.extend([
                MentorScheduleSegmentVO.reservation_to_segment(r, user_id)
                for r in reservations
            ])
            segments.sort(key=lambda s: s.dtstart)

            if next_dtstart is not None:
                segments = [s for s in segments if s.dtstart >= next_dtstart]

            res: MentorScheduleQueryVO = MentorScheduleQueryVO()
            if limit and len(segments) > limit:
                res.next_dtstart = segments[limit].dtstart
                segments = segments[:limit]
            res.segments = segments
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
        if new_timeslots:
            merged_timeslots += new_timeslots
        if exist_timeslots:
            merged_timeslots += exist_timeslots

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
