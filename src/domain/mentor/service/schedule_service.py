import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import DATETIME_FORMAT
from src.config.constant import ScheduleType
from src.config.exception import (
    raise_http_exception,
    ClientException,
)
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.domain.mentor.model.mentor_model import (
    TimeSlotDTO,
    MentorScheduleDTO,
    TimeSlotVO,
    MentorScheduleVO,
)
from src.infra.db.orm.init.user_init import MentorSchedule as Schedule
from src.infra.util.time_util import (
    expand_occurrences,
    month_range_ts,
    overlaps,
)

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
    ) -> MentorScheduleVO:
        # 回傳該 mentor 於指定年月「尚未被預約」且「未被 FORBIDDEN 覆蓋」的可用時段
        try:
            window_start, window_end = month_range_ts(dt_year, dt_month)

            allow_rows, forbid_rows, reservations = await asyncio.gather(
                self.__schedule_repository.get_month_schedules(
                    db, user_id, dt_year, dt_month, ScheduleType.ALLOW),
                self.__schedule_repository.get_month_schedules(
                    db, user_id, dt_year, dt_month, ScheduleType.FORBIDDEN),
                self.__schedule_repository.get_accepted_reservations_of_mentor(
                    db, user_id, window_start, window_end),
            )

            allow_occurrences = self.__expand_schedules(
                allow_rows, window_start, window_end)
            forbid_occurrences = self.__expand_schedules(
                forbid_rows, window_start, window_end)
            busy_intervals: List[Tuple[int, int]] = (
                [(b_start, b_end) for (b_start, b_end, _) in forbid_occurrences]
                + [(int(r.dtstart), int(r.dtend)) for r in reservations]
            )

            free_occurrences = [
                occ for occ in allow_occurrences
                if not self.__is_busy(occ[0], occ[1], busy_intervals)
            ]
            free_occurrences.sort(key=lambda o: o[0])

            if next_dtstart is not None:
                free_occurrences = [o for o in free_occurrences if o[0] >= next_dtstart]

            res: MentorScheduleVO = MentorScheduleVO()
            if limit and len(free_occurrences) > limit:
                res.next_dtstart = free_occurrences[limit][0]
                free_occurrences = free_occurrences[:limit]

            res.timeslots = [
                self.__occurrence_to_vo(src_dto, occ_start, occ_end)
                for (occ_start, occ_end, src_dto) in free_occurrences
            ]
            return res
        except Exception as e:
            log.error('get_schedule_list error: %s', str(e))
            raise_http_exception(e, msg='Schedule list not found')

    def __expand_schedules(
        self,
        schedules: List[TimeSlotDTO],
        window_start: int,
        window_end: int,
    ) -> List[Tuple[int, int, TimeSlotDTO]]:
        occurrences: List[Tuple[int, int, TimeSlotDTO]] = []
        for src in schedules:
            for (occ_start, occ_end) in expand_occurrences(
                dtstart=src.dtstart,
                dtend=src.dtend,
                rrule=src.rrule,
                exdate=src.exdate,
                dt_format=DATETIME_FORMAT,
                window_start=window_start,
                window_end=window_end,
            ):
                occurrences.append((occ_start, occ_end, src))
        return occurrences

    @staticmethod
    def __is_busy(a_start: int, a_end: int, busy: List[Tuple[int, int]]) -> bool:
        for (b_start, b_end) in busy:
            if overlaps(a_start, a_end, b_start, b_end):
                return True
        return False

    @staticmethod
    def __occurrence_to_vo(src: TimeSlotDTO, occ_start: int, occ_end: int) -> TimeSlotVO:
        # 展開後的 occurrence 以原始 schedule 的欄位為基底，覆寫 dtstart/dtend
        # id 保留原始 schedule.id，前端以 (id, dtstart) 辨識特定 occurrence
        data = src.model_dump()
        data['dtstart'] = occ_start
        data['dtend'] = occ_end
        return TimeSlotVO(**data)


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
