from typing import Optional

from sqlalchemy import Select, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ActivityService, ActivityStatus, RoleType
from src.infra.db.orm.init.user_init import Activity


class ActivityRepository:

    async def find_by_reservation_id_and_role(
        self,
        db: AsyncSession,
        reservation_id: int,
        role: RoleType,
    ) -> Optional[Activity]:
        if role == RoleType.MENTOR:
            stmt: Select = select(Activity).where(
                Activity.mentor_reservation_id == reservation_id,
            )
        else:
            stmt: Select = select(Activity).where(
                Activity.mentee_reservation_id == reservation_id,
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_scheduled(
        self,
        db: AsyncSession,
        event_id: str,
        mentor_reservation_id: int,
        mentee_reservation_id: int,
    ) -> None:
        stmt = insert(Activity).values(
            id=event_id,
            mentor_reservation_id=mentor_reservation_id,
            mentee_reservation_id=mentee_reservation_id,
            service=ActivityService.GOOGLE,
            status=ActivityStatus.SCHEDULED,
        )
        await db.execute(stmt)
        await db.commit()

    async def update_to_cancelled(
        self,
        db: AsyncSession,
        event_id: str,
    ) -> None:
        stmt = (
            update(Activity)
            .where(Activity.id == event_id)
            .values(status=ActivityStatus.CANCELLED)
        )
        await db.execute(stmt)
        await db.commit()
