import logging as log
from typing import List, Optional

from pydantic import BaseModel

from .common_model import ProfessionVO, InterestListVO

log.basicConfig(filemode='w', level=log.INFO)


class ProfileDTO(BaseModel):
    user_id: Optional[int]
    name: Optional[str]
    avatar: Optional[str]
    timezone: Optional[int]
    industry: Optional[int]
    position: Optional[str]
    company: Optional[str]
    linkedin_profile: Optional[str]
    interested_positions: Optional[List[int]]
    skills: Optional[List[int]]
    topics: Optional[List[int]]


class ProfileVO(BaseModel):
    user_id: int
    name: Optional[str]
    avatar: Optional[str]
    timezone: Optional[int]
    industry: Optional[ProfessionVO]
    position: Optional[str]
    company: Optional[str]
    linkedin_profile: Optional[str]
    interested_positions: Optional[InterestListVO] = []
    skills: Optional[InterestListVO] = []
    topics: Optional[InterestListVO] = []
