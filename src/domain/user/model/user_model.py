import logging as log
from typing import List, Optional, Union

from pydantic import BaseModel

from .common_model import ProfessionVO, InterestListVO

log.basicConfig(filemode='w', level=log.INFO)


class ProfileDTO(BaseModel):
    user_id: Optional[int]
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    industry: Optional[int] = None
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[int] = 0
    region: Optional[str] = ''
    linkedin_profile: Optional[str] = ''
    interested_positions: Optional[List[Union[str]]] = []
    skills: Optional[List[Union[str]]] = []
    topics: Optional[List[Union[str]]] = []
    language: Optional[str] = 'CHT'


class ProfileVO(BaseModel):
    user_id: int
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    industry: Optional[ProfessionVO] = None
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[int] = 0
    region: Optional[str] = ''
    linkedin_profile: Optional[str] = ''
    interested_positions: Optional[InterestListVO] = None
    skills: Optional[InterestListVO] = None
    topics: Optional[InterestListVO] = None
    language: Optional[str] = 'CHT'

    @staticmethod
    def of(model: ProfileDTO) -> 'ProfileVO':
        return ProfileVO(
            user_id=model.user_id,
            name=model.name,
            avatar=model.avatar,
            job_title=model.job_title,
            company=model.company,
            years_of_experience=model.years_of_experience,
            region=model.region,
            linkedin_profile=model.linkedin_profile
        )
