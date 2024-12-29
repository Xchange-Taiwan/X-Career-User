import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *
from ....infra.db.orm.init.user_init import MentorExperience

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceDTO(BaseModel):
    id: Optional[int] = None
    category: ExperienceCategory = None
    mentor_experiences_metadata: Dict = {}
    order: int = 0


class ExperienceVO(BaseModel):
    id: int
    category: ExperienceCategory = None
    mentor_experiences_metadata: Dict = {}
    order: int = 0

    @staticmethod
    def of(mentor_exp: MentorExperience):
        return ExperienceVO(id=mentor_exp.id,
                            category=mentor_exp.category,
                            mentor_experiences_metadata=mentor_exp.mentor_experiences_metadata,
                            order=mentor_exp.order)


class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []
