import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from ....config.constant import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class InterestVO(BaseModel):
    id: int
    category: InterestCategory = None
    subject_group: Optional[str] = None
    language: Optional[str]
    subject: Optional[str] = ''
    desc: Optional[Dict] = {}


class InterestListVO(BaseModel):
    interests: List[InterestVO] = []
    language: Optional[str] = None
    
    def to_json(self):
        result = self.json()
        return json.loads(result)


class ProfessionDTO(BaseModel):
    id: int
    category: ProfessionCategory = None
    language: Optional[str] = None


class ProfessionVO(ProfessionDTO):
    subject_group: Optional[str] = None
    subject: Optional[str] = ''
    profession_metadata: Optional[Dict] = {}


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []
    language: Optional[str]

    def to_json(self):
        result = self.json()
        return json.loads(result)
