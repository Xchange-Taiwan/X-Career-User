from typing import List, Dict, Any, Optional

from sqlalchemy import select, Select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import BookingStatus, RoleType, ScheduleType
from src.infra.db.orm.init.user_init import (
    MentorSchedule as Schedule,
    Reservation,
)
from src.infra.util.convert_util import (
    get_all_template, 
    bulk_insert,
    convert_dto_to_model,
)
from src.domain.mentor.model.mentor_model import TimeSlotDTO


class ScheduleRepository:

    async def get_month_schedules_all_types(
        self,
        db: AsyncSession,
        user_id: int,
        dt_year: int,
        dt_month: int,
    ) -> List[TimeSlotDTO]:
        # 單次查詢撈出當月 ALLOW/FORBIDDEN，減少 round-trip 次數
        stmt: Select = (
            select(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.dt_year == dt_year,
                Schedule.dt_month == dt_month,
                Schedule.dt_type.in_([
                    ScheduleType.ALLOW.value,
                    ScheduleType.FORBIDDEN.value,
                ]),
            )
            .order_by(Schedule.dtstart)
        )
        schedules: List[Optional[Schedule]] = await get_all_template(db, stmt)
        return [TimeSlotDTO.model_validate(s) for s in schedules if s]

    async def get_month_schedules(
        self,
        db: AsyncSession,
        user_id: int,
        dt_year: int,
        dt_month: int,
        dt_type: ScheduleType,
    ) -> List[TimeSlotDTO]:
        # 以 (user_id, dt_year, dt_month) 命中既有複合索引，並依 dt_type 分流
        stmt: Select = (
            select(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.dt_year == dt_year,
                Schedule.dt_month == dt_month,
                Schedule.dt_type == dt_type.value,
            )
            .order_by(Schedule.dtstart)
        )
        schedules: List[Optional[Schedule]] = await get_all_template(db, stmt)
        return [TimeSlotDTO.model_validate(s) for s in schedules if s]

    async def get_accepted_reservations_of_mentor(
        self,
        db: AsyncSession,
        mentor_user_id: int,
        window_start_ts: int,
        window_end_ts: int,
    ) -> List[Reservation]:
        # mentor 自己這一側已 ACCEPT 的預約即視為時段被佔用
        # 條件命中 idx_reservation_user_my_status_dtstart_dtend
        stmt: Select = select(Reservation).filter(
            Reservation.my_user_id == mentor_user_id,
            Reservation.my_role == RoleType.MENTOR.value,
            Reservation.my_status == BookingStatus.ACCEPT.value,
            Reservation.dtend > window_start_ts,
            Reservation.dtstart < window_end_ts,
        )
        return list(await get_all_template(db, stmt))


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
    
    async def delete_all_by_user_id(self, db: AsyncSession, user_id: int) -> int:
        stmt = delete(Schedule).where(Schedule.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

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
