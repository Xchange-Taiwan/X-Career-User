import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceDTO(BaseModel):
    user_id: Optional[int]
    language: str
    desc: Dict
    order: int



class ExperienceVO(BaseModel):
    user_id: int
    category: ExperienceCategory
    language: str
    desc: Dict
    order: int


class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []
