from typing import Dict

from ..enum.mentor_enums import SeniorityLevel
from ...user.model.common_model import ProfessionListVO
from ...user.model.user_model import *
from ....config.conf import *
from ....config.constant import *

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
    expertises: Optional[List[int]]



class ProfessionsDTO(BaseModel):
    professions_id: int
    category: Optional[str]
    subject: Optional[str] = ''
    professions_metadata: Optional[Dict] = {}


class CannedMessageDTO(BaseModel):
    canned_message_id: int
    user_id: int
    role: Optional[str]
    message: Optional[str]


class MentorProfileVO(ProfileVO):
    personal_statement: Optional[str] = ""
    about: Optional[str] = ""
    seniority_level: Optional[SeniorityLevel] = ""
    expertises: Optional[ProfessionListVO] = None


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
