import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from ....config.constant import *
import logging as log

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
