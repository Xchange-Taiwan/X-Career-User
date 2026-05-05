from typing import List, Optional

from sqlalchemy import select, Select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import BookingStatus, RoleType, ScheduleType
from src.infra.db.orm.init.user_init import (
    MentorSchedule as Schedule,
    Reservation,
)
from src.infra.util.convert_util import (
    get_all_template,
    get_first_template,
    bulk_insert,
    convert_dto_to_model,
)
from src.domain.mentor.model.mentor_model import TimeSlotDTO


class ScheduleRepository:

    async def get_by_id(self, db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        # ORM row, not the Pydantic projection — booking validation needs the
        # raw fields (rrule, exdate, meeting_duration_minutes) to expand the
        # legal sub-slot set for this schedule.
        stmt: Select = select(Schedule).where(Schedule.id == schedule_id)
        return await get_first_template(db, stmt)

    async def get_forbidden_for_user(
        self, db: AsyncSession, user_id: int,
    ) -> List[Schedule]:
        # FORBIDDEN rows are typically a small per-user set (one-off blocks),
        # so we fetch them all and let the caller do precise overlap+rrule
        # expansion. Keeping this coarse avoids missing rows whose stored
        # (dtstart,dtend) underestimates the actual reach of an rrule.
        stmt: Select = select(Schedule).where(
            and_(
                Schedule.user_id == user_id,
                Schedule.dt_type == ScheduleType.FORBIDDEN.value,
            )
        )
        return list(await get_all_template(db, stmt))

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

    async def get_schedule_related_reservations_of_mentor(
        self,
        db: AsyncSession,
        mentor_user_id: int,
        window_start_ts: int,
        window_end_ts: int,
    ) -> List[Reservation]:
        # mentor 自己這一側為 ACCEPT/PENDING 的預約都要回傳到 schedule segments
        # 但對方若已 REJECT 就視同預約結束,不該佔住時段
        # (對方取消時只會更新 status,不會動到 mentor 的 my_status)
        # 條件命中 idx_reservation_user_my_status_dtstart_dtend
        stmt: Select = select(Reservation).filter(
            Reservation.my_user_id == mentor_user_id,
            Reservation.my_status.in_([
                BookingStatus.ACCEPT.value,
                BookingStatus.PENDING.value,
            ]),
            Reservation.status.in_([
                BookingStatus.ACCEPT.value,
                BookingStatus.PENDING.value,
            ]),
            Reservation.my_role == RoleType.MENTOR.value,
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
            
        except Exception:
            await db.rollback()
            raise
    
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
