import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

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
    TagVO,
)

log = logging.getLogger(__name__)


# Maps every (kind, intent) we accept to the field name used on
# MentorProfileDTO/VO. position/HAVE is intentionally absent — mentors offer
# skills/topics, not positions. Order is the canonical bucket order used in
# both API responses and the SQS payload.
_BUCKET_BY_KIND_INTENT: Dict[Tuple[str, str], str] = {
    (TagKind.POSITION.value, TagIntent.WANT.value): 'want_position',
    (TagKind.SKILL.value,    TagIntent.WANT.value): 'want_skill',
    (TagKind.TOPIC.value,    TagIntent.WANT.value): 'want_topic',
    (TagKind.SKILL.value,    TagIntent.HAVE.value): 'have_skill',
    (TagKind.TOPIC.value,    TagIntent.HAVE.value): 'have_topic',
}

_WANT_BUCKETS = ('want_position', 'want_skill', 'want_topic')
_HAVE_BUCKETS = ('have_skill', 'have_topic')

_BUCKET_TO_KIND: Dict[str, TagKind] = {
    'want_position': TagKind.POSITION,
    'want_skill':    TagKind.SKILL,
    'want_topic':    TagKind.TOPIC,
    'have_skill':    TagKind.SKILL,
    'have_topic':    TagKind.TOPIC,
}


class TagService:
    def __init__(self, tag_repository: TagRepository):
        self.__tag_repository: TagRepository = tag_repository

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Bucket merge (write path) and hydrate (read path)
    # ------------------------------------------------------------------
    async def merge_buckets_to_arrays(
        self,
        db: AsyncSession,
        current_want_tags: List[str],
        current_have_tags: List[str],
        language: str,
        *,
        want_position: Optional[List[str]] = None,
        want_skill: Optional[List[str]] = None,
        want_topic: Optional[List[str]] = None,
        have_skill: Optional[List[str]] = None,
        have_topic: Optional[List[str]] = None,
    ) -> Tuple[List[str], List[str]]:
        # Per-bucket replace semantics: None = keep existing items of that
        # (kind, intent) untouched, [] = clear that bucket, [...] = replace.
        # Existing items whose kind we can't resolve from the catalog are
        # preserved untouched (don't drop user data on lookup misses).
        try:
            inputs = {
                'want_position': want_position,
                'want_skill': want_skill,
                'want_topic': want_topic,
                'have_skill': have_skill,
                'have_topic': have_topic,
            }
            replaced_buckets = {b for b, v in inputs.items() if v is not None}

            existing_kind_by_sg = await self._lookup_kinds(
                db, list(set(current_want_tags) | set(current_have_tags)), language
            )

            new_want = self._preserve_unreplaced(
                current_want_tags, existing_kind_by_sg,
                intent=TagIntent.WANT, replaced=replaced_buckets,
            )
            new_have = self._preserve_unreplaced(
                current_have_tags, existing_kind_by_sg,
                intent=TagIntent.HAVE, replaced=replaced_buckets,
            )

            # Validate + append new items per replaced bucket. Validation runs
            # inside the same transaction so auto-created orphan leaves are
            # rolled back on failure together with the profile upsert.
            for bucket in _WANT_BUCKETS:
                if inputs[bucket] is not None:
                    leaves = await self._validate_leaves(
                        db, _BUCKET_TO_KIND[bucket], inputs[bucket], language,
                    )
                    new_want.extend(leaf.subject_group for leaf in leaves)

            for bucket in _HAVE_BUCKETS:
                if inputs[bucket] is not None:
                    leaves = await self._validate_leaves(
                        db, _BUCKET_TO_KIND[bucket], inputs[bucket], language,
                    )
                    new_have.extend(leaf.subject_group for leaf in leaves)

            return _dedup(new_want), _dedup(new_have)
        except ClientException:
            raise
        except Exception as e:
            log.error("merge_buckets_to_arrays error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def hydrate_buckets(
        self,
        db: AsyncSession,
        want_tags: List[str],
        have_tags: List[str],
        language: str,
    ) -> Dict[str, List[TagVO]]:
        # Single bulk JOIN of all tagged subject_groups, then bucketed by
        # (intent=array origin, kind=catalog row). Items not found in the
        # catalog drop out — they don't belong to any bucket.
        result: Dict[str, List[TagVO]] = {b: [] for b in _BUCKET_BY_KIND_INTENT.values()}
        all_sgs = list(set(want_tags) | set(have_tags))
        if not all_sgs:
            return result

        try:
            rows = await self.__tag_repository.find_leaves_by_subject_groups(
                db, all_sgs, language,
            )
            tag_by_sg: Dict[str, object] = {row.subject_group: row for row in rows}

            for intent, source in ((TagIntent.WANT, want_tags), (TagIntent.HAVE, have_tags)):
                for sg in source:
                    tag = tag_by_sg.get(sg)
                    if tag is None:
                        continue
                    bucket = _BUCKET_BY_KIND_INTENT.get((tag.kind, intent.value))
                    if bucket is None:
                        # e.g. position/HAVE — not a valid combination; skip.
                        continue
                    result[bucket].append(TagVO.model_validate(tag))
            return result
        except Exception as e:
            log.error("hydrate_buckets error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _validate_leaves(
        self,
        db: AsyncSession,
        kind: TagKind,
        subject_groups: List[str],
        language: str,
    ) -> List[object]:
        # Find-or-create per subject_group inside the caller's transaction.
        # Group rows are catalog scaffolding — reject them so user selections
        # always reference leaves; rows missing from the catalog are
        # auto-created as orphans for a later seed pass to link.
        leaves: List[object] = []
        for sg in subject_groups:
            tag = await self.__tag_repository.find_tag(db, kind.value, sg, language)
            if tag is None:
                tag = await self.__tag_repository.create_tag(
                    db, kind.value, sg, language,
                )
            elif tag.is_group:
                raise ClientException(
                    msg=(
                        f"subject_group '{sg}' is a top-level group; "
                        f"user selections must reference leaf tags."
                    )
                )
            leaves.append(tag)
        return leaves

    async def _lookup_kinds(
        self,
        db: AsyncSession,
        subject_groups: List[str],
        language: str,
    ) -> Dict[str, str]:
        if not subject_groups:
            return {}
        rows = await self.__tag_repository.find_leaves_by_subject_groups(
            db, subject_groups, language,
        )
        return {row.subject_group: row.kind for row in rows}

    @staticmethod
    def _preserve_unreplaced(
        current: List[str],
        kind_by_sg: Dict[str, str],
        intent: TagIntent,
        replaced: set,
    ) -> List[str]:
        kept: List[str] = []
        for sg in current:
            kind = kind_by_sg.get(sg)
            bucket = (
                _BUCKET_BY_KIND_INTENT.get((kind, intent.value))
                if kind is not None else None
            )
            # Unresolvable items (no catalog match) stay put — don't lose
            # user data on lookup misses.
            if bucket is None or bucket not in replaced:
                kept.append(sg)
        return kept


def _dedup(items: List[str]) -> List[str]:
    # dict.fromkeys preserves first-seen order, which matters for the SQS
    # payload + GET response staying stable across writes.
    return list(dict.fromkeys(items))
