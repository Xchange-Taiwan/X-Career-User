from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.orm.init.user_init import CannedMessage


class CannedMessageRepository:

    async def delete_all_by_user_id(self, db: AsyncSession, user_id: int) -> int:
        stmt = delete(CannedMessage).where(CannedMessage.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount
