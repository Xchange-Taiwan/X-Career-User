import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import TagKind
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


# Two intent-side maps replace what was a (kind, intent) tuple lookup —
# intent now means "which array (want_tags vs have_tags) the subject_group
# is stored in", so it never needs to round-trip through an enum.
# position/HAVE is intentionally absent — mentors offer skills/topics, not
# positions.
_WANT_BUCKET_BY_KIND: Dict[str, str] = {
    TagKind.POSITION.value: 'want_position',
    TagKind.SKILL.value:    'want_skill',
    TagKind.TOPIC.value:    'want_topic',
}
_HAVE_BUCKET_BY_KIND: Dict[str, str] = {
    TagKind.SKILL.value: 'have_skill',
    TagKind.TOPIC.value: 'have_topic',
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
        # Strict invariant: parent_subject_group IS NULL ⇔ group row;
        # NOT NULL ⇔ leaf. _validate_leaves rejects writes that would
        # break this, so orphan leaves can't accumulate.
        try:
            rows = await self.__tag_repository.list_catalog(db, kind, language)

            groups_by_key: dict = {}
            ordered_keys: List[str] = []

            for tag in rows:
                if tag.parent_subject_group is None:
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
                    # Leaf whose parent isn't in this language gets dropped —
                    # the catalog is mis-seeded and pretending otherwise hides
                    # the bug.

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
    # Flat-kind reads (industry-style — no leaf/group hierarchy)
    # ------------------------------------------------------------------
    async def hydrate_flat_tag(
        self,
        db: AsyncSession,
        kind: TagKind,
        subject_group: Optional[str],
        language: str,
    ) -> Optional[TagVO]:
        # For attributes stored as a single subject_group on profiles
        # (e.g. profiles.industry). Returns None on missing/empty input
        # or stale catalog match — callers decide whether that's an error.
        if not subject_group:
            return None
        try:
            row = await self.__tag_repository.find_tag(
                db, kind.value, subject_group, language,
            )
            if row is None:
                return None
            return TagVO.model_validate(row)
        except Exception as e:
            log.error("hydrate_flat_tag error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def list_tags_by_kind(
        self,
        db: AsyncSession,
        kind: TagKind,
        language: str,
    ) -> List[TagVO]:
        # Catalog listing for flat-kinds (industry). Hierarchical kinds
        # should use get_catalog so leaves nest under groups.
        try:
            rows = await self.__tag_repository.get_tags_by_kind(
                db, kind, language,
            )
            return [TagVO.model_validate(r) for r in rows]
        except Exception as e:
            log.error("list_tags_by_kind error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

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
                bucket_by_kind=_WANT_BUCKET_BY_KIND, replaced=replaced_buckets,
            )
            new_have = self._preserve_unreplaced(
                current_have_tags, existing_kind_by_sg,
                bucket_by_kind=_HAVE_BUCKET_BY_KIND, replaced=replaced_buckets,
            )

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
        # (which-array, kind=catalog row). Items not found in the catalog
        # drop out — they don't belong to any bucket.
        result: Dict[str, List[TagVO]] = {
            'want_position': [], 'want_skill': [], 'want_topic': [],
            'have_skill': [], 'have_topic': [],
        }
        all_sgs = list(set(want_tags) | set(have_tags))
        if not all_sgs:
            return result

        try:
            rows = await self.__tag_repository.find_leaves_by_subject_groups(
                db, all_sgs, language,
            )
            tag_by_sg: Dict[str, object] = {row.subject_group: row for row in rows}

            for source, bucket_by_kind in (
                (want_tags, _WANT_BUCKET_BY_KIND),
                (have_tags, _HAVE_BUCKET_BY_KIND),
            ):
                for sg in source:
                    tag = tag_by_sg.get(sg)
                    if tag is None:
                        continue
                    bucket = bucket_by_kind.get(tag.kind)
                    if bucket is None:
                        # e.g. position written into have_tags somehow —
                        # not a valid combination; skip rather than crash.
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
        # Strict: subject_groups must already exist as leaves in the catalog
        # (parent_subject_group is set). Unknown rows or top-level groups
        # are rejected so user writes can't drift the catalog.
        leaves: List[object] = []
        for sg in subject_groups:
            tag = await self.__tag_repository.find_tag(db, kind.value, sg, language)
            if tag is None:
                raise ClientException(
                    msg=(
                        f"unknown subject_group '{sg}' for kind={kind.value}; "
                        f"seed the catalog first."
                    )
                )
            if tag.parent_subject_group is None:
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
        bucket_by_kind: Dict[str, str],
        replaced: set,
    ) -> List[str]:
        kept: List[str] = []
        for sg in current:
            kind = kind_by_sg.get(sg)
            bucket = bucket_by_kind.get(kind) if kind is not None else None
            # Unresolvable items (no catalog match) stay put — don't lose
            # user data on lookup misses.
            if bucket is None or bucket not in replaced:
                kept.append(sg)
        return kept


def _dedup(items: List[str]) -> List[str]:
    # dict.fromkeys preserves first-seen order, which matters for the SQS
    # payload + GET response staying stable across writes.
    return list(dict.fromkeys(items))
