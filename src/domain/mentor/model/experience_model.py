import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceDTO(BaseModel):
    id: Optional[int]
    desc: Dict
    order: int



class ExperienceVO(BaseModel):
    id: int
    category: ExperienceCategory
    desc: Dict
    order: int


class ExperienceListVO(BaseModel):
    experiences: List[ExperienceVO] = []
