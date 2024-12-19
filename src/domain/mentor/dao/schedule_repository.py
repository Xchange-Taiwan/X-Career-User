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
        # Separate existing and new schedules
        exist_schedules = [schedule for schedule in schedules if schedule.id]
        new_schedules = [schedule for schedule in schedules if not schedule.id]

        # Update existing schedules,
        # NOTE: there's no bulk update function
        for exist_schedule in exist_schedules:
            exist_schedule = await db.merge(exist_schedule)

        # Insert new schedules
        if new_schedules:
            # 將 __dict__ 轉換為字典並移除 id 欄位
            insert_data = []
            for schedule in new_schedules:
                data = schedule.__dict__.copy()
                data.pop('id', None)  # 移除 id
                data.pop('_sa_instance_state', None)  # 移除 SQLAlchemy 的內部狀態
                insert_data.append(data)

            # NOTE: batch insert
            result = await db.execute(Schedule.__table__.insert().returning(*Schedule.__table__.c), 
                insert_data)
            # Update new schedules with database values
            for i, row in enumerate(result.fetchall()):
                for key, value in row._mapping.items():
                    setattr(new_schedules[i], key, value)

        await db.commit()
        return schedules

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
