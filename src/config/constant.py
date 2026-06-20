from enum import Enum


class Language(str, Enum):
    EN_US = 'en_US'
    ZH_TW = 'zh_TW'


class ExperienceCategory(str, Enum):
    WORK = 'WORK'
    EDUCATION = 'EDUCATION'
    LINK = 'LINK'
    WHAT_I_OFFER = 'WHAT_I_OFFER'


class SeniorityLevel(str, Enum):
    NO_REVEAL = 'NO REVEAL'
    JUNIOR = 'JUNIOR'
    INTERMEDIATE = 'INTERMEDIATE'
    SENIOR = 'SENIOR'
    STAFF = 'STAFF'
    MANAGER = 'MANAGER'


class ScheduleType(str, Enum):
    ALLOW = 'ALLOW'
    FORBIDDEN = 'FORBIDDEN'
    BOOKED = 'BOOKED'
    PENDING = 'PENDING'


class RoleType(str, Enum):
    MENTOR = 'MENTOR'
    MENTEE = 'MENTEE'


class BookingStatus(str, Enum):
    PENDING = 'PENDING'
    ACCEPT = 'ACCEPT'
    REJECT = 'REJECT'


class ReservationListState(str, Enum):
    MENTOR_UPCOMING = 'MENTOR_UPCOMING'
    MENTEE_UPCOMING = 'MENTEE_UPCOMING'
    MENTOR_PENDING = 'MENTOR_PENDING'
    MENTEE_PENDING = 'MENTEE_PENDING'
    MENTOR_HISTORY = 'MENTOR_HISTORY'
    MENTEE_HISTORY = 'MENTEE_HISTORY'

class ActivityService(str, Enum):
    GOOGLE = 'GOOGLE'


class ActivityStatus(str, Enum):
    SCHEDULED = 'SCHEDULED'
    CANCELLED = 'CANCELLED'

class SortingBy(str, Enum):
    UPDATED_TIME = 'UPDATED_TIME'
    # VIEW = 'VIEW'


class Sorting(Enum):
    ASC = 1
    DESC = -1


class TagKind(str, Enum):
    # The 5 mentor profile buckets are (kind × array): want_tags carries
    # position/skill/topic; have_tags carries skill/topic. Intent is
    # implicit in *which* array a subject_group lives in — no separate
    # enum needed.
    SKILL = 'skill'
    POSITION = 'position'
    TOPIC = 'topic'
    # Flat-kind: every row has parent_subject_group=NULL (no leaf/group
    # hierarchy). Stored on profiles.industry, not in want_tags/have_tags —
    # industry is a self-attribute (mentor and mentee both have one),
    # not a WANT/HAVE intent. Use hydrate_flat_tag / list_tags_by_kind.
    INDUSTRY = 'industry'
