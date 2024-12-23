from typing import Dict, Tuple
from pydantic import Field
from datetime import datetime

from ..enum.mentor_enums import SeniorityLevel
from ...user.model.common_model import ProfessionListVO
from ...user.model.user_model import *
from ....config.conf import *
from ....config.constant import *
from ....config.exception import ClientException
from ....infra.util.time_util import (
    create_calendar_with_rrule,
    rrule_events,
)

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
    expertises: Optional[List[str]]


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
    dt_type: str = Field(..., example=AVAILABLE_EVT,
                         pattern=f'^({AVAILABLE_EVT}|{UNAVAILABLE_EVT})$')
    dt_year: Optional[int] = Field(default=None, example=2024)
    dt_month: Optional[int] = Field(default=None, example=6)
    dtstart: int = Field(..., example=1717203600)
    dtend: int = Field(..., example=1717207200)
    timezone: str = Field(default='UTC', example='UTC')
    rrule: Optional[str] = Field(default=None, example='FREQ=WEEKLY;COUNT=4')
    exdate: List[Optional[int]] = Field(
        default=[], example=[1718413200, 1719622800])

    class Config:
        from_attributes = True  # orm_mode = True
        # json_encoders = {
        #     datetime: lambda v: v.strftime(DATETIME_FORMAT)
        # }

    @staticmethod
    def min_dtstart_and_max_dtend(dtos: List['TimeSlotDTO']) -> Tuple[int, int]:
        min_dtstart, max_dtend = 9999999999, 0
        for timeslot in dtos:
            min_dtstart = min(min_dtstart, timeslot.dtstart)
            max_dtend = max(max_dtend, timeslot.dtend)
        return (min_dtstart, max_dtend)

    # for list sorting

    @staticmethod
    def sort_by_dtend(dto: 'TimeSlotDTO') -> int:
        return dto.dtend

    # Check Conflicts by Greedy Algorithm

    @staticmethod
    def opverlapping_interval_check(timeslots: List['TimeSlotDTO']):
        # timeslots.sort(key=TimeSlotDTO.sort_by_dtend)
        timeslots = TimeSlotDTO.sort_with_rrule(timeslots)
        if len(timeslots) < 2:
            raise ClientException(msg='Parse iCalendar rrule error')

        first_timeslot = timeslots[0]
        last_timeslot = timeslots[len(timeslots) - 1]

        conflicts = 0
        prev_timeslot = timeslots[0]
        conflict_records: Dict = {}

        # 跳過第 0 個，從第 1 個開始算起
        for timeslot in timeslots[1:]:
            if timeslot.dtstart < prev_timeslot.dtend:
                conflicts += 1
                conflict_records.update({
                    prev_timeslot.hash(): prev_timeslot.to_json(),
                    timeslot.hash(): timeslot.to_json(),
                })
            else:
                prev_timeslot = timeslot

        if conflicts > 0:
            be = 'is' if conflicts == 1 else 'are'
            noun = 'conflict' if conflicts == 1 else 'conflicts'
            first_yearmonth = f'{first_timeslot.dt_year}/{first_timeslot.dt_month}'
            last_yearmonth = f'{last_timeslot.dt_year}/{last_timeslot.dt_month}'
            conflict_records = [record for record in conflict_records.values()]
            if first_yearmonth == last_yearmonth:
                raise ClientException(msg=f'There {be} {conflicts} {noun} in {first_yearmonth}',
                                      data={'conflicts': conflict_records})

            raise ClientException(msg=f'There {be} {conflicts} {noun} between {first_yearmonth} and {last_yearmonth}',
                                  data={'conflicts': conflict_records})

    @staticmethod
    def sort_with_rrule(timeslots: List['TimeSlotDTO']):
        # get MIN_DTSTART
        (MIN_DTSTART, max_dtend) = TimeSlotDTO.min_dtstart_and_max_dtend(timeslots)

        all_timeslots = []
        for timeslot in timeslots:
            if not timeslot.rrule:
                all_timeslots.append(timeslot)
            else:
                copies_with_rrule = \
                    TimeSlotDTO.get_copies_by_rrule(timeslot, MIN_DTSTART)
                all_timeslots.extend(copies_with_rrule)

        all_timeslots.sort(key=TimeSlotDTO.sort_by_dtend)
        return all_timeslots

    # Check recurring events in the time range

    @staticmethod
    def get_copies_by_rrule(timeslot: 'TimeSlotDTO', MIN_DTSTART: int):
        start_date = datetime.fromtimestamp(timeslot.dtstart)
        end_date = datetime.fromtimestamp(timeslot.dtend)

        # Create a iCalendar
        calendar = create_calendar_with_rrule(
            event_title=timeslot.dt_type,
            start_date=start_date,  # format: datetime
            end_date=end_date,      # format: datetime
            dt_format=DATETIME_FORMAT,
            rrule=timeslot.rrule,
        )

        # Parse the iCalendar and generate all event instances
        timeslot_copies = []
        FINAL_DTEND = datetime.fromtimestamp(MIN_DTSTART + MAX_PERIOD_SECS)
        events = rrule_events(calendar, start_date, FINAL_DTEND)

        # Traverse all events and output
        for event in events:
            timeslot_copy = timeslot.model_copy()
            timeslot_copy.dtstart = event.get('DTSTART').dt.timestamp()
            timeslot_copy.dtend = event.get('DTEND').dt.timestamp()
            timeslot_copies.append(timeslot_copy)
        return timeslot_copies

    def hash(self):
        srt_timestamp = int(self.dtstart)
        end_timestamp = int(self.dtend)
        # 不考慮 exdate, 除非整個流程考慮 exdate
        if self.rrule:
            return hash((self.dt_type, srt_timestamp, end_timestamp, self.rrule,))
        return hash((self.dt_type, srt_timestamp, end_timestamp,))

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
        # make sure all fields are in correct type
        if isinstance(self.dtstart, float):
            self.dtstart = int(self.dtstart)
        if isinstance(self.dtend, float):
            self.dtend = int(self.dtend)
        self.exdate = [int(ex) if isinstance(ex, float) else ex for ex in self.exdate]

        return self.model_dump()


class TimeSlotVO(TimeSlotDTO):
    id: int

    @staticmethod
    def of(dto: TimeSlotDTO):
        if (dto is None):
            return None
        dto_dict = dto.__dict__
        for exclude in ['created_at', 'updated_at']:
            dto_dict.pop(exclude, None)
        return TimeSlotVO(**dto_dict)


class MentorScheduleVO(BaseModel):
    timeslots: Optional[List[TimeSlotVO]] = Field(default=[])
    next_dtstart: Optional[int] = Field(default=None, example=0)

    def to_json(self) -> Dict:
        timeslots: Dict = [timeslot.to_json() for timeslot in self.timeslots]
        return {
            'timeslots': timeslots,
            'next_dtstart': self.next_dtstart,
        }
