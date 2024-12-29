from typing import List, Optional
from sqlalchemy import func, Integer, Select, select, update, insert, join, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.conf import BATCH, RESERVATION_ISOLAION_LEVEL
from src.domain.user.model.reservation_model import *
from src.infra.db.orm.init.user_init import *
from src.infra.util.convert_util import (
    get_first_template,
    get_all_template,
    fetch_all_template,
    convert_dto_to_model,
)


class ReservationRepository:

    async def find_by_id(self, db: AsyncSession,
                         reserve_id: int,
                         my_user_id) -> Optional[ReservationVO]:
        stmt: Select = select(Reservation).where(
            and_(
                Reservation.id == reserve_id,
                Reservation.my_user_id == my_user_id,
            )
        )
        reservation = await get_first_template(db, stmt)
        if not reservation:
            return None
        return ReservationVO.model_validate(reservation)


    async def find_one(self, db: AsyncSession,
                       query: Dict) -> Optional[ReservationVO]:
        stmt: Select = select(Reservation).filter_by(**query)
        reservation = await get_first_template(db, stmt)
        if not reservation:
            return None
        return ReservationVO.model_validate(reservation)


    async def find_all(self, db: AsyncSession,
                       query: Dict,
                       dtstart: Optional[int] = None,
                       dtend: Optional[int] = None) -> Optional[List[ReservationVO]]:
        stmt: Select = select(Reservation).filter_by(**query)
        if dtstart:
            stmt = stmt.filter(Reservation.dtstart >= dtstart)
        if dtend:
            stmt = stmt.filter(Reservation.dtend <= dtend)

        reservations = await get_all_template(db, stmt)
        return [ReservationVO.model_validate(reservation) for reservation in reservations]


    async def save_all(self, db: AsyncSession, reservations: List[Reservation]):
        for reservation in reservations:
            await self.save(db, reservation)
        await db.commit()


    async def save(self, db: AsyncSession, reservation: Reservation):
        if reservation.id:
            # 構建更新語句
            stmt = update(Reservation).where(
                (Reservation.id == reservation.id) &
                (Reservation.my_user_id == reservation.my_user_id)
            ).values(
                my_status=reservation.my_status,
                status=reservation.status,
                messages=reservation.messages,
            ).execution_options(synchronize_session="fetch")

        else:
            # 構建插入語句
            stmt = insert(Reservation).values(
                schedule_id=reservation.schedule_id,
                dtstart=reservation.dtstart,
                dtend=reservation.dtend,
                my_user_id=reservation.my_user_id,
                my_status=reservation.my_status,
                user_id=reservation.user_id,
                status=reservation.status,
                messages=reservation.messages,
                previous_reserve=reservation.previous_reserve,
            ).returning(Reservation.id)

        result = await db.execute(stmt)
        await db.flush()  # 將更改發送到數據庫，但不提交事務




    async def get_user_reservations(self, db: AsyncSession,
                                    user_id: int,
                                    query: ReservationQueryDTO) -> Optional[List[ReservationDTO]]:
        stmt = select(
            Reservation.id,
            Reservation.schedule_id,
            Reservation.dtstart,
            Reservation.dtend,
            Reservation.my_user_id,
            Reservation.my_status,
            Reservation.user_id,
            Reservation.status,
            Reservation.messages,
            Reservation.previous_reserve,
            Profile.user_id.label('user_id'),
            Profile.name,
            Profile.avatar,
            Profile.job_title,
            Profile.years_of_experience,
        ).select_from(
            join(Reservation, Profile, (Reservation.user_id == Profile.user_id))
        )
        # for key, value in query.items():
        #     stmt = stmt.where(getattr(Reservation, key) == value)
        stmt = stmt.where(Reservation.my_user_id == user_id)

        if query.state == ReservationListState.UPCOMING:
            stmt = stmt.where(
                (Reservation.my_status == BookingStatus.ACCEPT) &
                (Reservation.status == BookingStatus.ACCEPT) &
                (Reservation.dtend >= func.now())
            )
        elif query.state == ReservationListState.PENDING:
            stmt = stmt.where(
                ((Reservation.my_status == BookingStatus.PENDING) |
                (Reservation.status == BookingStatus.PENDING)) &
                (Reservation.dtend >= func.now())
            )
        elif query.state == ReservationListState.HISTORY:
            stmt = stmt.where(
                (Reservation.my_status == BookingStatus.REJECT) |
                (Reservation.status == BookingStatus.REJECT) |
                (Reservation.dtend < func.now())
            )

        if query.next_dtend:
            stmt = stmt.where(Reservation.dtend <= query.next_dtend)

        stmt = stmt.order_by(Reservation.dtend.desc()).limit(query.batch)
        result = await db.execute(stmt)
        reservations = result.fetchall()

        return [ReservationInfoVO.from_sender_model(reservation) for reservation in reservations]
