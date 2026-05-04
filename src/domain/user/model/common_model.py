import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from ....config.constant import *
import logging

log = logging.getLogger(__name__)


class ProfessionDTO(BaseModel):
    id: int
    category: ProfessionCategory = None
    language: Optional[str] = ''


class ProfessionVO(ProfessionDTO):
    subject_group: str = 'unknown'
    subject: str = ''
    profession_metadata: Dict = {}
    language: Optional[str] = ''

    class Config:
        from_attributes = True # orm_mode = True

    @classmethod
    def from_tag(cls, tag, category: ProfessionCategory) -> 'ProfessionVO':
        # Compat adapter while the legacy /industries response shape (and
        # ProfileVO.industry) still uses ProfessionVO. Source of truth is
        # the unified `tags` table — this just remaps field names. Drops
        # in #233 once the frontend cuts over to /tags.
        return cls(
            id=tag.id,
            category=category,
            subject_group=tag.subject_group,
            subject=tag.subject or '',
            profession_metadata=(tag.desc or {}),
            language=tag.language or '',
        )


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []

    def to_json(self):
        result = self.json()
        return json.loads(result)
