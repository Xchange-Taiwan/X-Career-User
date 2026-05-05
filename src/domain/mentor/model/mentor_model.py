from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from ...user.model.tag_model import TagVO
from ...user.model.user_model import *
from .experience_model import ExperienceVO
from ....config.conf import *
from ....config.constant import *
from ....config.exception import ClientException, UnprocessableClientException
from src.infra.util.time_util import (
    create_calendar_with_rrule,
    rrule_events,
)

log = logging.getLogger(__name__)


class MentorProfileDTO(ProfileDTO):
    personal_statement: Optional[str] = None
    about: Optional[str] = None
    seniority_level: Optional[SeniorityLevel] = None

    # Input buckets — leaf subject_groups grouped by (intent, kind). Per
    # bucket: None = leave that bucket alone, [] = clear, [...] = replace.
    # Server validates leaves against the tags catalog and merges with
    # the existing storage arrays to produce profiles.want_tags / have_tags
    # — those columns intentionally never appear on this dto so the API
    # contract stays small.
    want_position: Optional[List[str]] = None
    want_skill: Optional[List[str]] = None
    want_topic: Optional[List[str]] = None
    have_skill: Optional[List[str]] = None
    have_topic: Optional[List[str]] = None

    class Config:
        from_attributes = True # orm_mode = True


class CannedMessageDTO(BaseModel):
    canned_messages_id: int
    user_id: int
    role: Optional[str]
    message: Optional[str]


class MentorProfileVO(ProfileVO):
    personal_statement: Optional[str] = ""
    about: Optional[str] = ""
    seniority_level: Optional[SeniorityLevel] = SeniorityLevel.NO_REVEAL
    experiences: Optional[List[ExperienceVO]] = Field(default_factory=list)

    # Hydrated tag buckets — each element is a full TagVO joined from the
    # catalog (subject, desc, parent_subject_group, etc.). None = not yet
    # hydrated; [] = no tags in that bucket.
    want_position: Optional[List[TagVO]] = None
    want_skill: Optional[List[TagVO]] = None
    want_topic: Optional[List[TagVO]] = None
    have_skill: Optional[List[TagVO]] = None
    have_topic: Optional[List[TagVO]] = None

    @staticmethod
    def of(mentor_profile_dto: MentorProfileDTO) -> 'MentorProfileVO':
        return MentorProfileVO(
            user_id=mentor_profile_dto.user_id,
            name=mentor_profile_dto.name,
            avatar=mentor_profile_dto.avatar,
            location=mentor_profile_dto.location,
            job_title=mentor_profile_dto.job_title,
            company=mentor_profile_dto.company,
            years_of_experience=mentor_profile_dto.years_of_experience,
            language=mentor_profile_dto.language,
            personal_statement=mentor_profile_dto.personal_statement,
            about=mentor_profile_dto.about,
            seniority_level=mentor_profile_dto.seniority_level,
            is_mentor=mentor_profile_dto.is_mentor,
        )

    def to_dto_json(self):
        # Search consumes flat subject_group arrays per bucket — full TagVO
        # would be wasted bytes on the wire (Search only filters by key).
        return {
            'user_id': self.user_id,
            'name': self.name,
            'avatar': self.avatar,
            'job_title': self.job_title,
            'company': self.company,
            'years_of_experience': self.years_of_experience,
            'location': self.location,
            'industry': getattr(self.industry, 'subject_group', None),
            'language': self.language,
            'is_mentor': self.is_mentor,
            'personal_statement': self.personal_statement,
            'about': self.about,
            'seniority_level': self.seniority_level.value if self.seniority_level else None,
            'experiences': jsonable_encoder(self.experiences),
            'want_position': self._tag_subject_groups(self.want_position),
            'want_skill': self._tag_subject_groups(self.want_skill),
            'want_topic': self._tag_subject_groups(self.want_topic),
            'have_skill': self._tag_subject_groups(self.have_skill),
            'have_topic': self._tag_subject_groups(self.have_topic),
        }

    @staticmethod
    def _tag_subject_groups(tags: Optional[List[TagVO]]) -> List[str]:
        if not tags:
            return []
        return [t.subject_group for t in tags if t.subject_group]


class TimeSlotDTO(BaseModel):
    id: Optional[int] = Field(None, example=0)
    user_id: int = Field(..., example=1)
    dt_type: str = Field(
        ...,
        example=ScheduleType.ALLOW.value,
        pattern=f'^({ScheduleType.ALLOW.value}|{ScheduleType.FORBIDDEN.value})$'
    )
    dt_year: Optional[int] = Field(default=None, example=2024)
    dt_month: Optional[int] = Field(default=None, example=6)
    dtstart: int = Field(
        ...,
        example=1717203600,
        description='Unix timestamp seconds in UTC (GMT+0)',
    )
    dtend: int = Field(
        ...,
        example=1717207200,
        description='Unix timestamp seconds in UTC (GMT+0)',
    )
    rrule: Optional[str] = Field(
        default=None,
        example='FREQ=WEEKLY;COUNT=4',
        description=(
            'Recurrence rule interpreted in UTC (GMT+0). '
            'New format: weekly/daily only. '
            'Legacy: FREQ=MINUTELY for sub-slot division — kept for backwards compat.'
        ),
    )
    timezone: str = Field(
        default='UTC',
        example='UTC',
        description='Must be UTC. Client and backend are fixed to GMT+0.',
    )
    exdate: List[Optional[int]] = Field(
        default=[],
        example=[1718413200, 1719622800],
        description='Excluded occurrence starts in Unix timestamp seconds UTC (GMT+0)',
    )
    meeting_duration_minutes: Optional[int] = Field(
        default=None,
        example=30,
        description=(
            'New format marker. When set, (dtstart, dtend) is a contiguous '
            'block divided into sub-slots of this length; rrule must NOT be '
            'FREQ=MINUTELY. NULL = legacy row whose rrule encodes sub-slot iteration.'
        ),
    )

    class Config:
        from_attributes = True  # orm_mode = True
        # json_encoders = {
        #     datetime: lambda v: v.strftime(DATETIME_FORMAT)
        # }

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
        # self.exdate = [int(ex) if isinstance(ex, float) else ex for ex in self.exdate]
        return self.model_dump()


class MentorScheduleDTO(BaseModel):
    until: int = Field(default=32503651200, example=1735689600)
    timeslots: List[TimeSlotDTO] = Field(default=[])

    def min_dtstart_to_max_dtend(self) -> Tuple[int, int]:
        if not self.timeslots:
            raise ValueError("No timeslots provided")

        min_dtstart = 9999999999
        for timeslot in self.timeslots:
            min_dtstart = min(min_dtstart, timeslot.dtstart)

        if self.until is None:
            raise ValueError("until field is required but not provided")

        return (min_dtstart, self.until)


    # Check Conflicts by Greedy Algorithm
    @classmethod
    def opverlapping_interval_check(cls, timeslots: List[TimeSlotDTO], UNTIL_TIMESTAMP: int):
        UNTIL_END_DATE = datetime.fromtimestamp(UNTIL_TIMESTAMP)
        expanded = cls.sort_with_rrule(timeslots, UNTIL_END_DATE)

        # rrule 展開失敗的早期偵測:輸入有 rrule 但展開後是空的
        if len(expanded) == 0:
            had_rrule = any(getattr(ts, 'rrule', None) for ts in timeslots)
            if had_rrule:
                raise UnprocessableClientException(msg='Failed to expand recurring events from rrule')
            return

        # ALLOW 與 FORBIDDEN 是不同的「層」:FORBIDDEN 的用途就是要蓋在
        # ALLOW 區間內挖洞,所以兩者之間的重疊不算 conflict。各自 type 內
        # 部仍維持「同 type 不可重疊」的限制。
        allow_slots = [ts for ts in expanded if ts.dt_type == ScheduleType.ALLOW.value]
        forbidden_slots = [ts for ts in expanded if ts.dt_type == ScheduleType.FORBIDDEN.value]

        conflicts = 0
        conflict_records: Dict = {}
        for group in (allow_slots, forbidden_slots):
            conflicts, conflict_records = cls._scan_group_conflicts(
                group, conflicts, conflict_records,
            )

        if conflicts > 0:
            first_timeslot = expanded[0]
            last_timeslot = expanded[-1]
            be = 'is' if conflicts == 1 else 'are'
            noun = 'conflict' if conflicts == 1 else 'conflicts'
            first_yearmonth = f'{first_timeslot.dt_year}/{first_timeslot.dt_month}'
            last_yearmonth = f'{last_timeslot.dt_year}/{last_timeslot.dt_month}'
            if first_yearmonth == last_yearmonth:
                raise ClientException(msg=f'There {be} {conflicts} {noun} in {first_yearmonth}',
                                      data={'conflicts': conflict_records})

            raise ClientException(msg=f'There {be} {conflicts} {noun} between {first_yearmonth} and {last_yearmonth}',
                                  data={'conflicts': conflict_records})

    @staticmethod
    def _scan_group_conflicts(
        group: List['TimeSlotDTO'],
        conflicts: int,
        conflict_records: Dict,
    ) -> Tuple[int, Dict]:
        if len(group) < 2:
            return conflicts, conflict_records
        prev = group[0]
        for ts in group[1:]:
            if ts.dtstart < prev.dtend:
                conflicts += 1
                conflict_records[conflicts] = [prev.to_json(), ts.to_json()]
            else:
                prev = ts
        return conflicts, conflict_records

    @classmethod
    def sort_with_rrule(cls, timeslots: List[TimeSlotDTO], UNTIL_END_DATE: datetime):
        all_timeslots = []
        for timeslot in timeslots:
            if not timeslot.rrule:
                all_timeslots.append(timeslot)
            else:
                copies_with_rrule = \
                    cls.get_copies_by_rrule(timeslot, UNTIL_END_DATE)
                all_timeslots.extend(copies_with_rrule)

        all_timeslots.sort(key=lambda dto: dto.dtend)
        return all_timeslots

    @classmethod
    def get_copies_by_rrule(cls, timeslot: TimeSlotDTO, UNTIL_END_DATE: datetime):
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
        events = rrule_events(calendar, start_date, UNTIL_END_DATE)

        # Traverse all events and output
        for event in events:
            timeslot_copy = timeslot.model_copy()
            timeslot_copy.dtstart = event.get('DTSTART').dt.timestamp()
            timeslot_copy.dtend = event.get('DTEND').dt.timestamp()
            timeslot_copies.append(timeslot_copy)
        return timeslot_copies


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


class MentorScheduleSegmentVO(BaseModel):
    id: Optional[int] = Field(default=None, example=0)
    user_id: int = Field(..., example=1)
    dt_type: str = Field(
        ...,
        example=ScheduleType.ALLOW.value,
        pattern=(
            f'^({ScheduleType.ALLOW.value}|{ScheduleType.FORBIDDEN.value}|'
            f'{ScheduleType.BOOKED.value}|{ScheduleType.PENDING.value})$'
        )
    )
    dtstart: int = Field(..., example=1717203600)
    dtend: int = Field(..., example=1717207200)
    rrule: Optional[str] = Field(default=None, example='FREQ=WEEKLY;COUNT=4')
    timezone: str = Field(default='UTC', example='UTC')
    exdate: List[Optional[int]] = Field(default=[], example=[1718413200, 1719622800])
    meeting_duration_minutes: Optional[int] = Field(default=None, example=30)
    source: str = Field(..., example='schedule')
    source_id: Optional[int] = Field(default=None, example=100)

    @staticmethod
    def timeslot_to_segment(
        src: TimeSlotDTO,
    ) -> "MentorScheduleSegmentVO":
        return MentorScheduleSegmentVO(
            id=src.id,
            user_id=src.user_id,
            dt_type=src.dt_type,
            dtstart=src.dtstart,
            dtend=src.dtend,
            rrule=src.rrule,
            timezone=src.timezone,
            exdate=src.exdate,
            meeting_duration_minutes=src.meeting_duration_minutes,
            source='schedule',
            source_id=src.id,
        )

    @staticmethod
    def reservation_to_segment(
        src: Any,
        user_id: int,
    ) -> "MentorScheduleSegmentVO":
        return MentorScheduleSegmentVO(
            user_id=user_id,
            dt_type=(
                ScheduleType.BOOKED.value
                if getattr(src.my_status, 'value', src.my_status) == BookingStatus.ACCEPT.value
                else ScheduleType.PENDING.value
            ),
            dtstart=int(src.dtstart),
            dtend=int(src.dtend),
            timezone='UTC',
            source='reservation',
            source_id=int(src.id),
        )

    def to_json(self):
        return self.model_dump()


class MentorScheduleQueryVO(BaseModel):
    segments: Optional[List[MentorScheduleSegmentVO]] = Field(default=[])
    next_dtstart: Optional[int] = Field(default=None, example=0)

    def to_json(self) -> Dict:
        segments: Dict = [segment.to_json() for segment in self.segments]
        return {
            'segments': segments,
            'next_dtstart': self.next_dtstart,
        }
