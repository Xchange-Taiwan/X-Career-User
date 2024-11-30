import logging as log
from typing import List, Optional

from pydantic import BaseModel

from .common_model import ProfessionVO, InterestListVO

log.basicConfig(filemode='w', level=log.INFO)


class ProfileDTO(BaseModel):
    user_id: Optional[int]
    name: Optional[str] = ""
    avatar: Optional[str] = ""
    location: Optional[str] = ""
    timezone: Optional[int] = None
    industry: Optional[int] = None
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    experience: Optional[int] = None
    linkedin_profile: Optional[str] = ""
    interested_positions: Optional[List[int]] = []
    skills: Optional[List[int]] = []
    topics: Optional[List[int]] = []
    language: Optional[str] = 'CHT'


class ProfileVO(BaseModel):
    user_id: Optional[int]
    name: Optional[str] = ""
    avatar: Optional[str] = ""
    location: Optional[str] = ""
    timezone: Optional[int] = None
    industry: Optional[int] = None
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    experience: Optional[int] = None
    linkedin_profile: Optional[str] = ""
    interested_positions: Optional[List[int]] = []
    skills: Optional[List[int]] = []
    topics: Optional[List[int]] = []
    language: Optional[str] = 'CHT'

    @staticmethod
    def of(model: ProfileDTO) -> 'ProfileVO':
        return ProfileVO(**model.model_dump())
