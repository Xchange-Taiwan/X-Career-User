from typing import List, Optional, Dict
from sqlalchemy import func, Integer, Select, select, update, insert, join, and_, bindparam
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
import logging

logging.basicConfig(filemode='w', level=log.INFO)

log = logging.getLogger(__name__)


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
        log.info(f"=== save_all 开始执行 ===")
        log.info(f"Reservations 数量: {len(reservations)}")
        
        # 分離更新和插入操作
        updates = [r for r in reservations if r.id]
        inserts = [r for r in reservations if not r.id]
        
        log.info(f"更新操作数量: {len(updates)}, 插入操作数量: {len(inserts)}")
        
        # 记录每个 reservation 的详细信息
        for i, r in enumerate(reservations):
            log.info(f"Reservation {i}: id={r.id}, my_role={r.my_role}, my_user_id={r.my_user_id}, schedule_id={r.schedule_id}")
        
        if updates:
            log.info("开始执行批量更新操作")
            # 批量更新
            stmt = update(Reservation).where(
                and_(
                    Reservation.id == bindparam('b_id'),
                    Reservation.my_user_id == bindparam('b_my_user_id')
                )
            ).values({
                'my_status': bindparam('b_my_status'),
                'status': bindparam('b_status'),
                'messages': bindparam('b_messages'),
            })
            
            for i, r in enumerate(updates):
                update_data = {
                    'b_id': r.id,
                    'b_my_user_id': r.my_user_id,
                    'b_my_status': r.my_status,
                    'b_status': r.status,
                    'b_messages': r.messages,
                }
                log.info(f"执行更新 {i}: {update_data}")
                await db.execute(stmt, update_data)  # N次 IO：多次更新
            log.info("批量更新操作完成")
        
        if inserts:
            log.info("开始执行批量插入操作")
            # 批量插入
            stmt = insert(Reservation).returning(Reservation.id)
            
            # 准备插入数据
            insert_data = [{
                'schedule_id': r.schedule_id,
                'dtstart': r.dtstart,
                'dtend': r.dtend,
                'my_user_id': r.my_user_id,
                'my_status': r.my_status,
                'user_id': r.user_id,
                'status': r.status,
                'my_role': r.my_role,
                'messages': r.messages,
                'previous_reserve': r.previous_reserve,
            } for r in inserts]
            
            log.info(f"插入数据: {insert_data}")
            
            result = await db.execute(stmt, insert_data)  # 1次 IO：批量插入
            log.info("插入操作执行完成")
            
            # 更新新插入記錄的 id
            new_ids = result.scalars().all()
            log.info(f"新插入记录的ID: {new_ids}")
            for r, new_id in zip(inserts, new_ids):
                r.id = new_id
                log.info(f"更新 reservation 对象 ID: {r.my_role} -> {new_id}")
        
        log.info("开始提交事务")
        await db.commit()  # 1次 IO：提交事務
        log.info("事务提交完成")


    async def save(self, db: AsyncSession, reservation: Reservation):
        log.info(f"=== save 开始执行 ===")
        log.info(f"Reservation: id={reservation.id}, my_role={reservation.my_role}, my_user_id={reservation.my_user_id}")
        
        if reservation.id:
            log.info("执行更新操作")
            # 構建更新語句
            stmt = update(Reservation).where(
                (Reservation.id == reservation.id) &
                (Reservation.my_user_id == reservation.my_user_id)
            ).values(
                my_status=reservation.my_status,
                status=reservation.status,
                messages=reservation.messages,
            ).execution_options(synchronize_session="fetch")
            await db.execute(stmt)  # 1次 IO：更新操作
            log.info("更新操作完成")

        else:
            log.info("执行插入操作")
            # 構建插入語句
            stmt = insert(Reservation).values(
                schedule_id=reservation.schedule_id,
                dtstart=reservation.dtstart,
                dtend=reservation.dtend,
                my_user_id=reservation.my_user_id,
                my_status=reservation.my_status,
                user_id=reservation.user_id,
                status=reservation.status,
                my_role=reservation.my_role,
                messages=reservation.messages,
                previous_reserve=reservation.previous_reserve,
            ).returning(Reservation.id)
            
            log.info(f"插入数据: schedule_id={reservation.schedule_id}, my_role={reservation.my_role}")
            
            result = await db.execute(stmt)  # 1次 IO：插入操作
            new_id = result.scalar_one()  # 從返回結果中獲取 id
            reservation.id = new_id  # 更新對象的 id
            log.info(f"插入成功，新ID: {new_id}")

        log.info("开始执行 flush 操作")
        await db.flush()  # 將更改發送到數據庫，但不提交事務
        log.info("flush 操作完成")


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
            Reservation.my_role,
            Reservation.messages,
            Reservation.previous_reserve,
            Profile.name,
            Profile.avatar,
            Profile.job_title,
            Profile.years_of_experience,
        ).select_from(
            join(
                Reservation, 
                Profile, 
                (Reservation.my_user_id == Profile.user_id or Reservation.user_id == Profile.user_id), 
                isouter=True
            )
        )
        # for key, value in query.items():
        #     stmt = stmt.where(getattr(Reservation, key) == value)
        stmt = stmt.where(Reservation.my_user_id == user_id)
        
        if query.state == ReservationListState.MENTOR_UPCOMING.value:
            stmt = stmt.where(
                (Reservation.my_status == BookingStatus.ACCEPT) &
                (Reservation.status == BookingStatus.ACCEPT) &
                (Reservation.my_role == RoleType.MENTOR) &
                (Reservation.dtend >= current_seconds())
            )
            if query.next_dtend:
                stmt = stmt.where(Reservation.dtend >= query.next_dtend)
                
        if query.state == ReservationListState.MENTEE_UPCOMING.value:
            stmt = stmt.where(
                (Reservation.my_status == BookingStatus.ACCEPT) &
                (Reservation.status == BookingStatus.ACCEPT) &
                (Reservation.my_role == RoleType.MENTEE) &
                (Reservation.dtend >= current_seconds())
            )
            if query.next_dtend:
                stmt = stmt.where(Reservation.dtend >= query.next_dtend)
                
        elif query.state == ReservationListState.MENTOR_PENDING.value:
            stmt = stmt.where(
                ((Reservation.my_status == BookingStatus.PENDING) |
                (Reservation.status == BookingStatus.PENDING)) &
                (Reservation.my_role == RoleType.MENTOR) &
                (Reservation.dtend >= current_seconds())
            )
            if query.next_dtend:
                stmt = stmt.where(Reservation.dtend >= query.next_dtend)
        
        elif query.state == ReservationListState.MENTEE_PENDING.value:
            stmt = stmt.where(
                ((Reservation.my_status == BookingStatus.PENDING) |
                (Reservation.status == BookingStatus.PENDING)) &
                (Reservation.my_role == RoleType.MENTEE) &
                (Reservation.dtend >= current_seconds())
            )
            if query.next_dtend:
                stmt = stmt.where(Reservation.dtend >= query.next_dtend)
                
        elif query.state == ReservationListState.HISTORY.value:
            stmt = stmt.where(
                (Reservation.my_status == BookingStatus.REJECT) |
                (Reservation.status == BookingStatus.REJECT) |
                (Reservation.dtend < current_seconds())
            )
            if query.next_dtend:
                stmt = stmt.where(Reservation.dtend <= query.next_dtend)
                

        stmt = stmt.order_by(Reservation.dtend.desc()).limit(query.batch)
        result = await db.execute(stmt)
        reservations = result.fetchall()

        reservation_dtos: List[ReservationInfoVO] = [ReservationInfoVO.from_sender_model(reservation) for reservation in reservations]
        return reservation_dtos
