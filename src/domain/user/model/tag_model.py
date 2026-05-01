from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.config.constant import TagIntent, TagKind


class TagVO(BaseModel):
    id: int
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''
    # Free-form display metadata (icon, color, etc.).
    desc: Optional[Dict[str, Any]] = None
    # NULL on group rows (and on flat-kind rows like industry); non-NULL on
    # leaves, pointing at the group's subject_group within the same kind.
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
    """User's tags pre-grouped by (kind, intent) — one bucket per frontend picker.

      want_skills    → (skill,    WANT)
      offer_skills   → (skill,    OFFER)
      want_topics    → (topic,    WANT)
      offer_topics   → (topic,    OFFER)
      want_positions → (position, WANT)
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
            # Unknown (kind, intent) pairs are dropped.
        return buckets


class UserTagBucketsInputDTO(BaseModel):
    """Replace-multiple-buckets payload. Per bucket:
      None   → leave untouched
      []     → clear
      [...]  → replace with these leaf subject_groups

    Language is intentionally not settable — server uses the profile's
    language so a write can't fork a user's tags across languages
    (current schema conflates concept and translation).
    """
    want_skills: Optional[List[str]] = None
    offer_skills: Optional[List[str]] = None
    want_topics: Optional[List[str]] = None
    offer_topics: Optional[List[str]] = None
    want_positions: Optional[List[str]] = None


class UserTagsUpsertDTO(BaseModel):
    # subject_groups must be leaves; group rows are catalog scaffolding,
    # not user selections, and the service rejects them.
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


class TagCatalogsVO(BaseModel):
    """Catalog response keyed by kind, so callers index `catalogs[kind]`
    uniformly whether they asked for one kind or all."""
    language: str
    catalogs: Dict[str, TagCatalogVO] = {}
