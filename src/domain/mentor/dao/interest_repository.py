from typing import List

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Optional, Type

from src.config.constant import InterestCategory
from src.infra.db.orm.init.user_init import Interest
from src.infra.util.convert_util import get_first_template, get_all_template


class InterestRepository:
    async def get_interest_by_ids(self, db: AsyncSession, ids: List[int]) -> list[Type[Interest]]:
        stmt = select(Interest).filter(Interest.id.in_(ids))
        res: List[Type[Interest]] = await get_all_template(db, stmt)
        return res

    async def get_interest_by_id(self, db: AsyncSession, interest_id: int) -> Optional[Type[Interest]]:
        stmt = select(Interest).filter(Interest.id == interest_id)
        res: Optional[Interest] = await get_first_template(db, stmt)
        return res

    async def get_by_interest(self, db: AsyncSession, interest: InterestCategory) -> Optional[Type[Interest]]:
        stmt = select(Interest).filter(Interest.category == interest)
        res: Optional[Interest] = await get_first_template(db, stmt)
        return res

    async def get_all_interest(self, db: AsyncSession) -> List[Type[Interest]]:
        stmt: Select = select(Interest)
        res: List[Type[Interest]] = await get_all_template(db, stmt)
        return res
