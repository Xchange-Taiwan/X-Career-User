import json
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *
from ....infra.db.orm.init.user_init import MentorExperience
import logging

log = logging.getLogger(__name__)


class ExperienceDTO(BaseModel):
    id: Optional[int] = None
    category: ExperienceCategory = None
    mentor_experiences_metadata: Dict = {}
    order: int = 0

    class Config:
        from_attributes = True


class ExperienceVO(BaseModel):
    id: int
    category: ExperienceCategory = None
    mentor_experiences_metadata: Dict = {}
    order: int = 0

    model_config = {
        "from_attributes": True
    }

    def to_json(self):
        result = self.model_dump_json()
        return json.loads(result)


class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []

    def to_json(self):
        result = self.model_dump_json()
        return json.loads(result)
