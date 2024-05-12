from typing import List, Optional, Type

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory
from src.infra.db.orm.init.user_init import Profession
from src.infra.util.convert_util import get_all_template, get_first_template


class ProfessionRepository:
    async def get_profession_by_ids(self, db: AsyncSession, ids: List[int]) -> List[Type[Profession]]:
        stmt: Select = select(Profession).filter(Profession.id.in_(ids))
        res: List[Type[Profession]] = await get_all_template(db, stmt)
        return res

    async def get_profession_by_id(self, db: AsyncSession, profession_id: int):
        stmt: Select = select(Profession).filter(Profession.id == profession_id)
        res: Optional[Profession] = await get_first_template(db, stmt)
        return res

    async def get_by_profession_category(self, db: AsyncSession, category: ProfessionCategory) -> Optional[
        Type[Profession]]:
        stmt: Select = select(Profession).filter(Profession.category == category)
        res: Optional[Profession] = await get_first_template(db, stmt)
        return res

    async def get_all_profession(self, db: AsyncSession) -> List[Type[Profession]]:
        stmt: Select = select(Profession)
        res: List[Type[Profession]] = await get_all_template(db, stmt)
        return res
