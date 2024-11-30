import logging as log
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *

log.basicConfig(filemode='w', level=log.INFO)


class InterestVO(BaseModel):
    id: int
    language: Optional[str] = None
    category: InterestCategory = None
    subject: Optional[str] = ''
    desc: Optional[Dict] = {}


class InterestListVO(BaseModel):
    interests: List[InterestVO] = []
    language: Optional[str] = None


class ProfessionDTO(BaseModel):
    id: int
    category: ProfessionCategory = None
    language: Optional[str] = ''


class ProfessionVO(ProfessionDTO):
    subject: str = ''
    profession_metadata: Dict = {}
    language: Optional[str] = ''


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []


