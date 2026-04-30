from typing import List, Optional, Type

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import TagKind
from src.infra.db.orm.init.user_init import Tag
from src.infra.util.convert_util import get_all_template, get_first_template


class TagRepository:
    async def get_tag_by_id(
        self, db: AsyncSession, tag_id: int
    ) -> Optional[Type[Tag]]:
        stmt: Select = select(Tag).filter(Tag.id == tag_id)
        return await get_first_template(db, stmt)

    async def get_tags_by_ids(
        self, db: AsyncSession, ids: List[int]
    ) -> List[Type[Tag]]:
        if not ids:
            return []
        stmt: Select = select(Tag).filter(Tag.id.in_(ids))
        return await get_all_template(db, stmt)

    async def get_tags_by_kind(
        self,
        db: AsyncSession,
        kind: TagKind,
        language: Optional[str] = None,
    ) -> List[Type[Tag]]:
        stmt: Select = select(Tag).filter(Tag.kind == kind.value)
        if language is not None:
            stmt = stmt.filter(Tag.language == language)
        return await get_all_template(db, stmt)
