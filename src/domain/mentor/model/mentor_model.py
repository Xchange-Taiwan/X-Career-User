import json
from typing import Dict

from fastapi.encoders import jsonable_encoder
from ...user.model.common_model import ProfessionListVO
from ...user.model.user_model import *
from .experience_model import ExperienceVO
from ....config.conf import *
from ....config.constant import *
from src.infra.db.orm.init.user_init import Profile, Profession

log.basicConfig(filemode='w', level=log.INFO)


# class MentorProfileDTO(BaseModel):
#     mentor_profile_id: Optional[int]
#     avatar: Optional[str]
#     location: Optional[str]
#     timezone: Optional[int]
#     experience: Optional[int]
#
#     personal_statement: Optional[str]
#     about: Optional[str]
#     # TODO: enum
#     seniority_level: Optional[str] = ""
#     expertises: Optional[List[ProfessionDTO]] = []


class MentorProfileDTO(ProfileDTO):
    personal_statement: Optional[str]
    about: Optional[str]
    seniority_level: Optional[SeniorityLevel]
    expertises: Optional[List[str]]

    class Config:
        from_attributes = True # orm_mode = True


class ProfessionDTO(BaseModel):
    professions_id: int
    category: Optional[str]
    subject: Optional[str] = ''
    profession_metadata: Optional[Dict] = {}


class CannedMessageDTO(BaseModel):
    canned_messages_id: int
    user_id: int
    role: Optional[str]
    message: Optional[str]


class MentorProfileVO(ProfileVO):
    personal_statement: Optional[str] = ""
    about: Optional[str] = ""
    seniority_level: Optional[SeniorityLevel] = SeniorityLevel.NO_REVEAL.value
    expertises: Optional[ProfessionListVO] = None
    experiences: Optional[List[ExperienceVO]] = []

    @staticmethod
    def of(mentor_profile_dto: MentorProfileDTO) -> 'MentorProfileVO':
        return MentorProfileVO(
            user_id=mentor_profile_dto.user_id,
            name=mentor_profile_dto.name,
            avatar=mentor_profile_dto.avatar,
            region=mentor_profile_dto.region,
            job_title=mentor_profile_dto.job_title,
            company=mentor_profile_dto.company,
            years_of_experience=mentor_profile_dto.years_of_experience,
            linkedin_profile=mentor_profile_dto.linkedin_profile,
            language=mentor_profile_dto.language,
            personal_statement=mentor_profile_dto.personal_statement,
            about=mentor_profile_dto.about,
            seniority_level=mentor_profile_dto.seniority_level
        )

    def from_dto(self):
        return MentorProfileDTO(
            user_id=self.user_id,
            name=self.name,
            avatar=self.avatar,
            job_title=self.job_title,
            company=self.company,
            years_of_experience=self.years_of_experience,
            region=self.region,
            linkedin_profile=self.linkedin_profile,
            interested_positions=self.i_to_subject_groups(self.interested_positions),
            skills=self.i_to_subject_groups(self.skills),
            topics=self.i_to_subject_groups(self.topics),
            # TODO: use 'industry' instead of ARRAY
            industries=self.p_to_subject_groups(self.industries),
            language=self.language,
            personal_statement=self.personal_statement,
            about=self.about,
            seniority_level=self.seniority_level,
            expertises=self.p_to_subject_groups(self.expertises),
        )

    def to_dto_json(self):
        dto = self.from_dto()
        dto_dict = jsonable_encoder(dto)
        dto_dict.update({'experiences': jsonable_encoder(self.experiences)})
        return dto_dict


class TimeSlotDTO(BaseModel):
    schedule_id: Optional[int]
    type: ScheduleType
    year: Optional[int] = SCHEDULE_YEAR
    month: Optional[int] = SCHEDULE_MONTH
    day_of_month: Optional[int] = SCHEDULE_DAY_OF_MONTH
    day_of_week: Optional[int] = SCHEDULE_DAY_OF_WEEK
    start_time: Optional[int]
    end_time: Optional[int]


class TimeSlotVO(TimeSlotDTO):
    schedule_id: int


class MentorScheduleVO(BaseModel):
    timeslots: Optional[List[TimeSlotVO]] = []
    next_id: Optional[int]
