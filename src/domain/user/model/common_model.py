import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from ....config.constant import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class InterestVO(BaseModel):
    id: int
    category: InterestCategory = None
    language: Optional[str] = None
    subject_group: str = 'unknown'
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
    language: Optional[str] = ''


class ProfessionVO(ProfessionDTO):
    subject_group: str = 'unknown'
    subject: str = ''
    profession_metadata: Dict = {}
    language: Optional[str] = ''

    class Config:
        from_attributes = True # orm_mode = True


class ProfessionListVO(BaseModel):
    professions: List[ProfessionVO] = []

    def to_json(self):
        result = self.json()
        return json.loads(result)
