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

    model_config = {"from_attributes": True}


class UserTagVO(BaseModel):
    tag_id: int
    intent: str
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''
    desc: Optional[Dict[str, Any]] = None


class UserTagListVO(BaseModel):
    user_tags: List[UserTagVO] = []


class UserTagsUpsertDTO(BaseModel):
    # Replace all of (user_id, kind, intent) with the supplied subject_groups.
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
