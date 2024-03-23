import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from ....config.constant import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class InterestVO(BaseModel):
    id: int
    category: InterestCategory
    subject: str
    desc: Dict


class InterestListVO(BaseModel):
    interests: List[InterestVO] = []


class ProfessionDTO(BaseModel):
    id: int
    category: ProfessionCategory


class ProfessionVO(ProfessionDTO):
    subject: str
    metadata: Dict


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []
