from typing import List, Dict, Any, Optional

from sqlalchemy import select, Select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.orm.init.user_init import MentorSchedule as Schedule
from src.infra.util.convert_util import (
    get_all_template, 
    bulk_insert,
    convert_dto_to_model,
)
from src.domain.mentor.model.mentor_model import TimeSlotDTO


class ScheduleRepository:
    
    async def get_schedule_list(self, db: AsyncSession, filter: Dict = {}, limit: Optional[int] = None, next_dtstart: Optional[int] = None) -> List[Optional[TimeSlotDTO]]:
        stmt: Select = select(Schedule).filter_by(**filter) \
            .order_by(Schedule.dtstart)

        if limit:
            stmt = stmt.limit(limit=limit)

        if next_dtstart:
            stmt = stmt.filter(Schedule.dtstart >= next_dtstart)

        schedules: List[Optional[Schedule]] = await get_all_template(db, stmt)
        timeslot_dtos: List[Optional[TimeSlotDTO]] = []
        for schedule in schedules:
            if schedule:
                timeslot_dtos.append(TimeSlotDTO.model_validate(schedule))

        return timeslot_dtos


    async def get_schedules_by_time_range(self, db: AsyncSession, user_id: int, dtstart: int, dtend: int):
        stmt: Select = select(Schedule).filter(
            and_(
                Schedule.user_id == user_id,
                Schedule.dtstart >= dtstart,
                Schedule.dtend <= dtend
            )
        )
        schedules: List[Optional[Schedule]] = await get_all_template(db, stmt)
        timeslot_dtos: List[Optional[TimeSlotDTO]] = []
        for schedule in schedules:
            if schedule:
                timeslot_dtos.append(TimeSlotDTO.model_validate(schedule))

        return timeslot_dtos


    async def save_schedules(self, db: AsyncSession, timeslot_dtos: List[TimeSlotDTO]) -> List[TimeSlotDTO]:
        try:
            schedules: List[Schedule] = [convert_dto_to_model(timeslot_dto, Schedule) for timeslot_dto in timeslot_dtos]

            # Separate existing and new schedules
            exist_schedules: List[Schedule] = [schedule for schedule in schedules if schedule.id]
            new_schedules: List[Schedule] = [schedule for schedule in schedules if not schedule.id]

            saved_schedules = []

            # Update first: update existing schedules
            for exist_schedule in exist_schedules:
                try:
                    merged_schedule = await db.merge(exist_schedule)
                    saved_schedules.append(merged_schedule)
                except Exception as merge_error:
                    print(f"Error merging schedule id {exist_schedule.id}: {merge_error}")
                    # 嘗試刷新連接並重試
                    await db.rollback()
                    merged_schedule = await db.merge(exist_schedule)
                    saved_schedules.append(merged_schedule)

            # Insert after: insert new schedules
            if new_schedules:
                try:
                    inserted_schedules = await bulk_insert(
                        db,
                        Schedule,
                        new_schedules,
                        ['id'], # 用於移除 primary keys 的欄位
                    )
                    saved_schedules.extend(inserted_schedules)
                except Exception as insert_error:
                    print(f"Error bulk inserting schedules: {insert_error}")
                    await db.rollback()
                    raise

            # 在 commit 之前轉換，避免 detached 狀態的 greenlet 錯誤
            timeslot_dtos: List[TimeSlotDTO] = [TimeSlotDTO.model_validate(schedule) for schedule in saved_schedules]
            await db.commit()
            return timeslot_dtos
            
        except Exception as e:
            await db.rollback()
            raise

        # merged_schedules = []
        # for schedule in schedules:
        #     # merge 會返回一個新的對象實例
        #     merged_schedule = await db.merge(schedule)
        #     merged_schedules.append(merged_schedule)

        # # 先提交確保所有更改都被保存
        # await db.commit()

        # # commit 後再進行 refresh
        # for schedule in merged_schedules:
        #     await db.refresh(schedule)

        # return merged_schedules
    
    async def delete_schedule(self, db: AsyncSession, user_id: int, schedule_id: int) -> int:
        stmt = select(Schedule).filter(Schedule.user_id == user_id) \
            .filter(Schedule.id == schedule_id)
        result = await db.execute(stmt)
        schedule = result.scalar_one_or_none()
        if schedule:
            await db.delete(schedule)
            await db.commit()
            return 1

        return 0
