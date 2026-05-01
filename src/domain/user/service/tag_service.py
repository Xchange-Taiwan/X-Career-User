import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import DEFAULT_LANGUAGE
from src.config.constant import TagIntent, TagKind
from src.config.exception import raise_http_exception
from src.domain.user.dao.tag_repository import TagRepository
from src.domain.user.model.tag_model import (
    UserTagListVO,
    UserTagsUpsertDTO,
    UserTagsUpsertVO,
    UserTagVO,
)

log = logging.getLogger(__name__)


class TagService:
    def __init__(self, tag_repository: TagRepository):
        self.__tag_repository: TagRepository = tag_repository

    async def list_user_tags(
        self,
        db: AsyncSession,
        user_id: int,
        kind: Optional[TagKind] = None,
        intent: Optional[TagIntent] = None,
    ) -> UserTagListVO:
        try:
            rows = await self.__tag_repository.get_user_tags_with_tag(
                db, user_id, kind=kind, intent=intent
            )
            user_tags = [
                UserTagVO(
                    tag_id=ut.tag_id,
                    intent=ut.intent,
                    kind=tag.kind,
                    subject_group=tag.subject_group,
                    language=tag.language,
                    subject=tag.subject,
                    desc=tag.desc,
                )
                for ut, tag in rows
            ]
            return UserTagListVO(user_tags=user_tags)
        except Exception as e:
            log.error("list_user_tags error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def replace_user_tags(
        self,
        db: AsyncSession,
        user_id: int,
        dto: UserTagsUpsertDTO,
    ) -> UserTagsUpsertVO:
        # Replace all (user_id, kind, intent) tags with the supplied
        # subject_groups. find-or-create canonical tag per subject_group,
        # then delete-existing + insert-new in a single transaction.
        try:
            language = dto.language or DEFAULT_LANGUAGE
            kind_value = dto.kind.value
            intent = dto.intent

            tag_ids: List[int] = []
            for subject_group in dto.subject_groups:
                tag = await self.__tag_repository.find_tag(
                    db, kind_value, subject_group, language
                )
                if tag is None:
                    tag = await self.__tag_repository.create_tag(
                        db, kind_value, subject_group, language
                    )
                tag_ids.append(tag.id)

            await self.__tag_repository.delete_user_tags_by_kind_intent(
                db, user_id, dto.kind, intent
            )
            for tag_id in tag_ids:
                await self.__tag_repository.upsert_user_tag(
                    db, user_id, tag_id, intent
                )

            await db.commit()
            return UserTagsUpsertVO(
                user_id=user_id,
                kind=kind_value,
                intent=intent.value,
                tag_ids=tag_ids,
                replaced=True,
            )
        except Exception as e:
            await db.rollback()
            log.error("replace_user_tags error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")
