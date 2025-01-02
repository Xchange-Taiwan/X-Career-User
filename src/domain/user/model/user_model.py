import json
from enum import Enum
from typing import List, Optional, Union, Dict, Set
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel
from src.config.constant import InterestCategory
from .common_model import (
    InterestListVO, ProfessionListVO, ProfessionVO,
)
import logging as log

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
    industry: Optional[str] = ''
    language: Optional[str] = 'zh_TW'
    
    class Config:
        from_attributes = True # orm_mode = True

    def get_all_subject_groups(self) -> List[str]:
        all = []
        if self.interested_positions:
            all += self.interested_positions
        if self.skills:
            all += self.skills
        if self.topics:
            all += self.topics
        return all

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
    industry: Optional[ProfessionVO] = None
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

    def i_to_subject_groups(self, interest_list: InterestListVO):
        if not interest_list:
            return []
        return [interest.subject_group for interest in interest_list.interests]

    def p_to_subject_groups(self, profession_list: ProfessionListVO):
        if not profession_list:
            return []
        return [profession.subject_group for profession in profession_list.professions]

    def to_json(self):
        result = self.model_dump_json()
        return json.loads(result)

    # def from_dto(self):
    #     return ProfileDTO(
    #         user_id=self.user_id,
    #         name=self.name,
    #         avatar=self.avatar,
    #         job_title=self.job_title,
    #         company=self.company,
    #         years_of_experience=self.years_of_experience,
    #         region=self.region,
    #         linkedin_profile=self.linkedin_profile,
    #         interested_positions=self.i_to_subject_groups(self.interested_positions),
    #         skills=self.i_to_subject_groups(self.skills),
    #         topics=self.i_to_subject_groups(self.topics),

    #         # TODO: use 'industry' instead of ARRAY
    #         industry=self.industry.subject_group,
    #         language=self.language,
    #     )

    # def to_dto_json(self):
    #     dto = self.from_dto()
    #     dto_dict = jsonable_encoder(dto)
    #     dto_dict.update({
    #         'personal_statement': None,
    #         'about': None,
    #         'seniority_level': None,
    #         'expertises': [],
    #         'experiences': [],
    #     })
    #     return dto_dict
