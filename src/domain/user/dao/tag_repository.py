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

    async def list_catalog(
        self,
        db: AsyncSession,
        kind: TagKind,
        language: str,
    ) -> List[Type[Tag]]:
        # Returns both group and leaf rows; service layer nests them.
        stmt: Select = (
            select(Tag)
            .filter(Tag.kind == kind.value)
            .filter(Tag.language == language)
            .order_by(Tag.parent_subject_group.nullsfirst(), Tag.subject_group)
        )
        return await get_all_template(db, stmt)

    async def find_tag(
        self,
        db: AsyncSession,
        kind: str,
        subject_group: str,
        language: str,
    ) -> Optional[Type[Tag]]:
        # When multiple subjects share a (kind, subject_group, language),
        # take the first — legacy writes only carried subject_group.
        stmt: Select = (
            select(Tag)
            .filter(Tag.kind == kind)
            .filter(Tag.subject_group == subject_group)
            .filter(Tag.language == language)
            .order_by(Tag.id)
            .limit(1)
        )
        return await get_first_template(db, stmt)

    async def find_leaves_by_subject_groups(
        self,
        db: AsyncSession,
        subject_groups: List[str],
        language: str,
    ) -> List[Type[Tag]]:
        # Bulk lookup for hydrating profile.want_tags/have_tags arrays at GET
        # time. Excludes group rows so callers can bucket by kind without
        # filtering scaffolding back out.
        if not subject_groups:
            return []
        stmt: Select = (
            select(Tag)
            .filter(Tag.subject_group.in_(subject_groups))
            .filter(Tag.language == language)
            .filter(Tag.is_group == False)  # noqa: E712
            .order_by(Tag.id)
        )
        return await get_all_template(db, stmt)

    async def create_tag(
        self,
        db: AsyncSession,
        kind: str,
        subject_group: str,
        language: str,
        subject: str = '',
    ) -> Tag:
        tag = Tag(
            kind=kind,
            subject_group=subject_group,
            language=language,
            subject=subject,
        )
        db.add(tag)
        await db.flush()
        return tag
