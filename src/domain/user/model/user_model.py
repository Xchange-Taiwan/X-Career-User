import json
import logging

from typing import List, Optional

from pydantic import BaseModel
from src.config.conf import DEFAULT_LANGUAGE
from .tag_model import TagVO

log = logging.getLogger(__name__)



class ProfileDTO(BaseModel):
    user_id: Optional[int]
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[str] = '0'
    location: Optional[str] = ''
    industry: Optional[str] = ''
    language: Optional[str] = DEFAULT_LANGUAGE
    is_mentor: Optional[bool] = False

    model_config = {
        "from_attributes": True
    }


class ProfileVO(BaseModel):
    user_id: int
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[str] = '0'
    location: Optional[str] = ''
    industry: Optional[TagVO] = None
    onboarding: Optional[bool] = False
    is_mentor: Optional[bool] = False
    language: Optional[str] = DEFAULT_LANGUAGE

    @staticmethod
    def of(model: ProfileDTO) -> 'ProfileVO':
        return ProfileVO(
            user_id=model.user_id,
            name=model.name,
            avatar=model.avatar,
            job_title=model.job_title,
            company=model.company,
            years_of_experience=model.years_of_experience,
            location=model.location,
            is_mentor=model.is_mentor,
        )

    def to_json(self):
        result = self.model_dump_json()
        return json.loads(result)
