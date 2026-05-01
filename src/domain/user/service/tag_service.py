import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import DEFAULT_LANGUAGE
from src.config.constant import TagIntent, TagKind
from src.config.exception import (
    ClientException,
    raise_http_exception,
)
from src.domain.user.dao.tag_repository import TagRepository
from src.domain.user.model.tag_model import (
    TagCatalogGroupVO,
    TagCatalogLeafVO,
    TagCatalogVO,
    TagCatalogsVO,
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
                    parent_subject_group=tag.parent_subject_group,
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
        # Find-or-create per subject_group, then delete-then-insert in one tx.
        # Group rows are rejected (must reference leaves); rows missing from
        # the catalog are auto-created as orphans (parent_subject_group=NULL)
        # for a later seed pass to link.
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
                elif tag.is_group:
                    raise ClientException(
                        msg=(
                            f"subject_group '{subject_group}' is a top-level "
                            f"group; user selections must reference leaf tags."
                        )
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
        except ClientException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("replace_user_tags error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def get_catalog(
        self,
        db: AsyncSession,
        kind: TagKind,
        language: str,
    ) -> TagCatalogVO:
        # Groups (is_group=TRUE) anchor the catalog; leaves attach via
        # parent_subject_group. Orphan leaves land in a synthetic catch-all
        # group so they aren't silently dropped.
        try:
            rows = await self.__tag_repository.list_catalog(db, kind, language)

            groups_by_key: dict = {}
            ordered_keys: List[str] = []
            orphan_leaves: List = []

            for tag in rows:
                if tag.is_group:
                    if tag.subject_group not in groups_by_key:
                        groups_by_key[tag.subject_group] = TagCatalogGroupVO(
                            subject_group=tag.subject_group,
                            subject=tag.subject or '',
                            language=tag.language,
                            desc=tag.desc,
                            leaves=[],
                        )
                        ordered_keys.append(tag.subject_group)
                else:
                    leaf = TagCatalogLeafVO(
                        tag_id=tag.id,
                        subject_group=tag.subject_group,
                        subject=tag.subject or '',
                        language=tag.language,
                        desc=tag.desc,
                    )
                    parent = groups_by_key.get(tag.parent_subject_group)
                    if parent is not None:
                        parent.leaves.append(leaf)
                    else:
                        orphan_leaves.append((tag.parent_subject_group, leaf))

            # Anything still here truly has no group row in this language.
            if orphan_leaves:
                catchall = TagCatalogGroupVO(
                    subject_group='',
                    subject='',
                    language=language,
                    leaves=[leaf for _, leaf in orphan_leaves],
                )
                groups_by_key[''] = catchall
                ordered_keys.append('')

            return TagCatalogVO(
                kind=kind.value,
                language=language,
                groups=[groups_by_key[k] for k in ordered_keys],
            )
        except Exception as e:
            log.error("get_catalog error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def get_catalogs(
        self,
        db: AsyncSession,
        kinds: Optional[List[TagKind]],
        language: str,
    ) -> TagCatalogsVO:
        # Sequential — AsyncSession isn't safe for concurrent ops on the
        # same session, so gather() would race.
        target_kinds = list(kinds) if kinds else list(TagKind)
        catalogs: dict = {}
        for k in target_kinds:
            vo = await self.get_catalog(db, k, language)
            catalogs[vo.kind] = vo
        return TagCatalogsVO(language=language, catalogs=catalogs)
