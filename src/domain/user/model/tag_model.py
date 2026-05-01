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
