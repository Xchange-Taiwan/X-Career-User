import json
from typing import Dict, List, Optional

from pydantic import BaseModel

from ....config.constant import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class InterestVO(BaseModel):
    id: int
    language: Optional[str]
    category: InterestCategory
    subject_group: str
    subject: str
    desc: Dict


class InterestListVO(BaseModel):
    interests: List[InterestVO] = []
    language: Optional[str]
    
    def to_json(self):
        result = self.json()
        return json.loads(result)


class ProfessionDTO(BaseModel):
    id: int
    category: ProfessionCategory
    language: Optional[str]


class ProfessionVO(ProfessionDTO):
    subject_group: str
    subject: str
    profession_metadata: Dict
    language: Optional[str]


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []
    
    def to_json(self):
        result = self.json()
        return json.loads(result)
