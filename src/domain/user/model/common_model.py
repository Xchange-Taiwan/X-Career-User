import logging as log
from typing import Dict, List

from pydantic import BaseModel

from ....config.constant import *

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
    profession_metadata: Dict


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []
