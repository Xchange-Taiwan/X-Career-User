from typing import List, Dict, Any, Optional

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import BATCH
from src.infra.db.orm.init.user_init import MentorSchedule as Schedule
from src.infra.util.convert_util import get_all_template, get_first_template


class ScheduleRepository:
    async def get_schedule_list(self, db: AsyncSession, filter: Dict = {}, limit: int = BATCH, next_id: Optional[int] = None) -> List[Optional[Schedule]]:
        stmt: Select = select(Schedule).filter_by(**filter) \
            .order_by(Schedule.dtstart) \
            .limit(limit=limit)
            
        if next_id:
            stmt = stmt.filter(Schedule.id >= next_id)

        res: List[Optional[Schedule]] = await get_all_template(db, stmt)
        return res
    
    async def save_schedules(self, db: AsyncSession, schedules: List[Schedule]) -> List[Schedule]:
        # Use bulk_save_objects for better performance
        db.add_all(schedules)
        await db.commit()

        # Refresh all schedules to get the latest ids
        for schedule in schedules:
            await db.refresh(schedule)

        return schedules
    
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
