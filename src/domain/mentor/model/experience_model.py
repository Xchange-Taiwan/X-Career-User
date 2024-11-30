import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *
from ....infra.db.orm.init.user_init import MentorExperience

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceDTO(BaseModel):
    user_id: Optional[int]
    desc: Dict = {}
    order: int = 0


class ExperienceVO(BaseModel):
    user_id: int
    category: ExperienceCategory = None
    desc: Dict = {}
    order: int = 0

    @staticmethod
    def of(mentor_exp: MentorExperience):
        return ExperienceVO(user_id=mentor_exp.user_id, category=mentor_exp.category, desc=mentor_exp.desc,
                            order=mentor_exp.order)


class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []
