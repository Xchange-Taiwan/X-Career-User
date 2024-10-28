import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *
from ....infra.db.orm.init.user_init import MentorExperience

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceDTO(BaseModel):
    user_id: Optional[int]
    desc: Dict
    order: int



class ExperienceVO(BaseModel):
    user_id: int
    category: ExperienceCategory
    desc: Dict
    order: int


    @staticmethod
    def of(mentor_exp: MentorExperience):
        vo = ExperienceVO()
        vo.user_id = mentor_exp.user_id
        vo.category = mentor_exp.category
        vo.desc = mentor_exp.desc
        vo.order = mentor_exp.order
        return vo





class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []
