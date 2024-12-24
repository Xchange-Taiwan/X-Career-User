import logging as log
from typing import List, Optional, Union, Dict, Set

from pydantic import BaseModel
from src.config.constant import InterestCategory
from .common_model import InterestListVO, ProfessionListVO

log.basicConfig(filemode='w', level=log.INFO)


class ProfileDTO(BaseModel):
    user_id: Optional[int]
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[int] = 0
    region: Optional[str] = ''
    linkedin_profile: Optional[str] = ''
    interested_positions: Optional[List[Union[str]]] = []
    skills: Optional[List[Union[str]]] = []
    topics: Optional[List[Union[str]]] = []
    industries: Optional[List[Union[str]]] = []
    language: Optional[str] = 'zh_TW'
    
    class Config:
        from_attributes = True # orm_mode = True

    def get_all_subject_groups(self) -> List[str]:
        return self.interested_positions + self.skills + self.topics

    def get_all_interest_details(self, all_interests: InterestListVO) -> Dict:
        interest_set: Set = { subject_group for subject_group in self.interested_positions }
        skill_set: Set = { subject_group for subject_group in self.skills }
        topic_set: Set = { subject_group for subject_group in self.topics }
        
        all_interest_details: Dict = {
            InterestCategory.INTERESTED_POSITION.value: [],
            InterestCategory.SKILL.value: [],
            InterestCategory.TOPIC.value: [],
        }
        
        for interest in all_interests.interests:
            if interest.subject_group in interest_set:
                all_interest_details[InterestCategory.INTERESTED_POSITION.value].append(interest)
            if interest.subject_group in skill_set:
                all_interest_details[InterestCategory.SKILL.value].append(interest)
            if interest.subject_group in topic_set:
                all_interest_details[InterestCategory.TOPIC.value].append(interest)

        return all_interest_details


class ProfileVO(BaseModel):
    user_id: int
    name: Optional[str] = ''
    avatar: Optional[str] = ''
    job_title: Optional[str] = ''
    company: Optional[str] = ''
    years_of_experience: Optional[int] = 0
    region: Optional[str] = ''
    linkedin_profile: Optional[str] = ''
    interested_positions: Optional[InterestListVO] = None
    skills: Optional[InterestListVO] = None
    topics: Optional[InterestListVO] = None
    industries: Optional[ProfessionListVO] = None
    on_boarding: Optional[bool] = False
    language: Optional[str] = 'zh_TW'

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
