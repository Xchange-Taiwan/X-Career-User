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
    location: Optional[str]
    personal_statement: Optional[str]
    about: Optional[str]
    seniority_level: Optional[SeniorityLevel]
    experience: Optional[int]
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
    # TODO: enum
    seniority_level: Optional[SeniorityLevel] = ""
    expertises: Optional[ProfessionListVO] = None

    @staticmethod
    def of(model: MentorProfileDTO) -> 'MentorProfileVO':
        res = MentorProfileVO(
            user_id=model.user_id,
            name=model.name,
            avatar=model.avatar,
            location=model.location,
            timezone=model.timezone,
            industry=model.industry,
            job_title=model.job_title,
            company=model.company,
            experience=model.experience,
            linkedin_profile=model.linkedin_profile,
            interested_positions=model.interested_positions,
            skills=model.skills,
            topics=model.topics,
            language=model.language,
            personal_statement=model.personal_statement,
            about=model.about,
            seniority_level=model.seniority_level,
            expertises=None
        )
        return res


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
