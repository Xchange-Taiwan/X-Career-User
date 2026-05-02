from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
