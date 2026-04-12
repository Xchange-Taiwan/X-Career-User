from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user.dao.reservation_repository import ReservationRepository


class DeleteAccountService:
    def __init__(self, reservation_repository: ReservationRepository):
        self.__reservation_repo = reservation_repository

    async def has_active_or_future_reservations(
        self, db: AsyncSession, user_id: int
    ) -> bool:
        return await self.__reservation_repo.has_active_or_future_reservations(db, user_id)
