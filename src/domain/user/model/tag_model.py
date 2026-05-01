from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.config.constant import TagIntent, TagKind


class TagVO(BaseModel):
    id: int
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''
    # Free-form per-tag metadata (icon, color, display hints, etc.) — mirrors
    # the v1 `_INTEREST_NESTED_PROPS.desc` JSONB field. Stored as Tag.desc.
    desc: Optional[Dict[str, Any]] = None
    # Two-layer hierarchy: NULL on top-level group rows (and on industry, which
    # is intentionally single-layer); non-NULL on leaf rows, where it points at
    # the group's `subject_group` within the same `kind`.
    parent_subject_group: Optional[str] = None

    model_config = {"from_attributes": True}


class UserTagVO(BaseModel):
    tag_id: int
    intent: str
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''
    desc: Optional[Dict[str, Any]] = None
    parent_subject_group: Optional[str] = None


class UserTagListVO(BaseModel):
    user_tags: List[UserTagVO] = []


class UserTagBucketsVO(BaseModel):
    """Pre-grouped view of a user's tags, keyed by the (kind, intent) pair
    that each frontend picker maps to. Saves the consumer from filtering the
    flat array by hand. The bucket names align with the existing form-field
    semantics so frontend reads/writes stay symmetric:

      want_skills    ↔  picker "想多了解、加強的技能"  (kind=skill,    intent=WANT)
      offer_skills   ↔  picker "我能教的 expertise"  (kind=skill,    intent=OFFER)
      want_topics    ↔  picker "想多了解的主題"     (kind=topic,    intent=WANT)
      offer_topics   ↔  picker "我能聊的主題"       (kind=topic,    intent=OFFER)
      want_positions ↔  picker "有興趣多了解的職位" (kind=position, intent=WANT)
    """
    want_skills: List[UserTagVO] = []
    offer_skills: List[UserTagVO] = []
    want_topics: List[UserTagVO] = []
    offer_topics: List[UserTagVO] = []
    want_positions: List[UserTagVO] = []

    @staticmethod
    def from_flat(tags: List[UserTagVO]) -> 'UserTagBucketsVO':
        buckets = UserTagBucketsVO()
        for t in tags:
            kind = t.kind
            intent = t.intent
            if kind == 'skill' and intent == 'WANT':
                buckets.want_skills.append(t)
            elif kind == 'skill' and intent == 'OFFER':
                buckets.offer_skills.append(t)
            elif kind == 'topic' and intent == 'WANT':
                buckets.want_topics.append(t)
            elif kind == 'topic' and intent == 'OFFER':
                buckets.offer_topics.append(t)
            elif kind == 'position' and intent == 'WANT':
                buckets.want_positions.append(t)
            # Unknown (kind, intent) pairs are dropped — the bucket model
            # exhaustively covers the supported axes; new pairs require an
            # explicit field addition here.
        return buckets


class UserTagsUpsertDTO(BaseModel):
    # Replace all of (user_id, kind, intent) with the supplied subject_groups.
    # `subject_groups` items must be LEAF subject_groups for kind ∈
    # {skill, position, topic} (group-level rows are catalog scaffolding,
    # not user selections). The service rejects non-leaf entries.
    kind: TagKind
    intent: TagIntent
    subject_groups: List[str] = []
    language: Optional[str] = None  # falls back to user's profile language


class UserTagsUpsertVO(BaseModel):
    user_id: int
    kind: str
    intent: str
    tag_ids: List[int] = []
    replaced: bool = True


class TagCatalogLeafVO(BaseModel):
    tag_id: int
    subject_group: str
    subject: str
    language: str
    desc: Optional[Dict[str, Any]] = None


class TagCatalogGroupVO(BaseModel):
    subject_group: str
    subject: str
    language: str
    desc: Optional[Dict[str, Any]] = None
    leaves: List[TagCatalogLeafVO] = []


class TagCatalogVO(BaseModel):
    kind: str
    language: str
    groups: List[TagCatalogGroupVO] = []
