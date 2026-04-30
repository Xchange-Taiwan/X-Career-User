from typing import List, Optional

from pydantic import BaseModel

from src.config.constant import TagIntent, TagKind


class TagVO(BaseModel):
    id: int
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''

    model_config = {"from_attributes": True}


class UserTagVO(BaseModel):
    tag_id: int
    intent: str
    kind: str
    subject_group: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = ''


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
