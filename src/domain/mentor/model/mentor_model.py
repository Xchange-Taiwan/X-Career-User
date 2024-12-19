from typing import Dict
from pydantic import Field
from datetime import datetime

from ..enum.mentor_enums import SeniorityLevel
from ...user.model.common_model import ProfessionListVO
from ...user.model.user_model import *
from ....config.conf import *
from ....config.constant import *
from ....infra.util.convert_util import json_encoders

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
#     seniority_level: Optional[str] = ''
#     expertises: Optional[List[ProfessionDTO]] = []


class MentorProfileDTO(ProfileDTO):
    personal_statement: Optional[str]
    about: Optional[str]
    seniority_level: Optional[SeniorityLevel]
    expertises: Optional[List[int]]



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
    personal_statement: Optional[str] = ''
    about: Optional[str] = ''
    seniority_level: Optional[SeniorityLevel] = ''
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
    id: Optional[int] = Field(None, example=0)
    user_id: int = Field(..., example=1)
    dt_type: str = Field(..., example=AVAILABLE_EVT, regex=f'^({AVAILABLE_EVT}|{UNAVAILABLE_EVT})$')
    dt_year: Optional[int] = Field(default=None, example=2024)
    dt_month: Optional[int] = Field(default=None, example=6)
    dtstart: int = Field(..., example=1717203600)
    dtend: int = Field(..., example=1717207200)
    timezone: str = Field(default='UTC', exclude='UTC')
    rrule: Optional[str] = Field(default=None, example='FREQ=WEEKLY;COUNT=4')
    exdate: List[Optional[int]] = Field(default=[], example=[1718413200, 1719622800])

    class Config:
        orm_mode = True
        # json_encoders = {
        #     datetime: lambda v: v.strftime(DATETIME_FORMAT)
        # }

    def init_fields(self, user_id: int) -> 'TimeSlotDTO':
        self.user_id = user_id
        if self.dtstart:
            date = datetime.fromtimestamp(self.dtstart)
        else:
            date = datetime.now()
        self.dt_year = date.year
        self.dt_month = date.month
        return self
    
    def to_json(self):
        return json_encoders(self)
        # return self.json()


class TimeSlotVO(TimeSlotDTO):
    id: int


class MentorScheduleVO(BaseModel):
    timeslots: Optional[List[TimeSlotVO]] = Field(default=[])
    next_id: Optional[int] = Field(default=None, example=0)
    
    def to_json(self) -> Dict:
        timeslots: Dict = [timeslot.to_json() for timeslot in self.timeslots]
        return {
            'timeslots': timeslots,
            'next_id': self.next_id,
        }
