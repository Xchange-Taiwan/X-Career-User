import json
from typing import Dict, List

from pydantic import BaseModel

from ....config.constant import *
import logging

log = logging.getLogger(__name__)


# Experiences ride inline on the profile row (profiles.experiences JSONB[]).
# No autoincrement id — the JSON array index is the only ordering signal we
# need; the explicit `order` field still survives for now because the
# frontend reads it for display ordering.
class ExperienceDTO(BaseModel):
    category: ExperienceCategory = None
    mentor_experiences_metadata: Dict = {}
    order: int = 0

    class Config:
        from_attributes = True


class ExperienceVO(BaseModel):
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
