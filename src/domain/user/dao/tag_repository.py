from typing import List, Optional, Type

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import TagIntent, TagKind
from src.infra.db.orm.init.user_init import Tag, UserTag
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

    async def get_user_tags(
        self,
        db: AsyncSession,
        user_id: int,
        kind: Optional[TagKind] = None,
        intent: Optional[TagIntent] = None,
    ) -> List[Type[UserTag]]:
        stmt: Select = select(UserTag).filter(UserTag.user_id == user_id)
        if intent is not None:
            stmt = stmt.filter(UserTag.intent == intent.value)
        if kind is not None:
            # join through Tag to filter by kind
            stmt = stmt.join(Tag, Tag.id == UserTag.tag_id).filter(
                Tag.kind == kind.value
            )
        return await get_all_template(db, stmt)

    async def get_user_tags_with_tag(
        self,
        db: AsyncSession,
        user_id: int,
        kind: Optional[TagKind] = None,
        intent: Optional[TagIntent] = None,
    ) -> List[tuple]:
        stmt: Select = (
            select(UserTag, Tag)
            .join(Tag, Tag.id == UserTag.tag_id)
            .filter(UserTag.user_id == user_id)
        )
        if intent is not None:
            stmt = stmt.filter(UserTag.intent == intent.value)
        if kind is not None:
            stmt = stmt.filter(Tag.kind == kind.value)
        result = await db.execute(stmt)
        return list(result.all())

    async def delete_user_tags_by_kind_intent(
        self,
        db: AsyncSession,
        user_id: int,
        kind: TagKind,
        intent: TagIntent,
    ) -> int:
        sub = select(Tag.id).filter(Tag.kind == kind.value)
        stmt = (
            delete(UserTag)
            .where(UserTag.user_id == user_id)
            .where(UserTag.intent == intent.value)
            .where(UserTag.tag_id.in_(sub))
        )
        result = await db.execute(stmt)
        return result.rowcount or 0

    async def upsert_user_tag(
        self,
        db: AsyncSession,
        user_id: int,
        tag_id: int,
        intent: TagIntent,
    ) -> None:
        # PK is (user_id, tag_id, intent); insert if absent, otherwise no-op.
        existing = await db.execute(
            select(UserTag)
            .filter(UserTag.user_id == user_id)
            .filter(UserTag.tag_id == tag_id)
            .filter(UserTag.intent == intent.value)
        )
        if existing.first():
            return
        db.add(
            UserTag(user_id=user_id, tag_id=tag_id, intent=intent.value)
        )
        await db.flush()
