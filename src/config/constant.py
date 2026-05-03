from enum import Enum


class Language(Enum):
    EN_US = 'en_US'
    ZH_TW = 'zh_TW'


class InterestCategory(Enum):
    INTERESTED_POSITION = 'INTERESTED_POSITION'
    SKILL = 'SKILL'
    TOPIC = 'TOPIC'


class ProfessionCategory(Enum):
    EXPERTISE = 'EXPERTISE'
    INDUSTRY = 'INDUSTRY'


class ExperienceCategory(Enum):
    WORK = 'WORK'
    EDUCATION = 'EDUCATION'
    LINK = 'LINK'
    WHAT_I_OFFER = 'WHAT_I_OFFER'


class SeniorityLevel(Enum):
    NO_REVEAL = 'NO REVEAL'
    JUNIOR = 'JUNIOR'
    INTERMEDIATE = 'INTERMEDIATE'
    SENIOR = 'SENIOR'
    STAFF = 'STAFF'
    MANAGER = 'MANAGER'


class ScheduleType(Enum):
    ALLOW = 'ALLOW'
    FORBIDDEN = 'FORBIDDEN'
    BOOKED = 'BOOKED'
    PENDING = 'PENDING'


class RoleType(Enum):
    MENTOR = 'MENTOR'
    MENTEE = 'MENTEE'


class BookingStatus(Enum):
    PENDING = 'PENDING'
    ACCEPT = 'ACCEPT'
    REJECT = 'REJECT'


class ReservationListState(Enum):
    MENTOR_UPCOMING = 'MENTOR_UPCOMING'
    MENTEE_UPCOMING = 'MENTEE_UPCOMING'
    MENTOR_PENDING = 'MENTOR_PENDING'
    MENTEE_PENDING = 'MENTEE_PENDING'
    MENTOR_HISTORY = 'MENTOR_HISTORY'
    MENTEE_HISTORY = 'MENTEE_HISTORY'

class ActivityService(Enum):
    GOOGLE = 'GOOGLE'


class ActivityStatus(Enum):
    SCHEDULED = 'SCHEDULED'
    CANCELLED = 'CANCELLED'

class SortingBy(Enum):
    UPDATED_TIME = 'UPDATED_TIME'
    # VIEW = 'VIEW'


class Sorting(Enum):
    ASC = 1
    DESC = -1


class TagKind(Enum):
    # The 5 mentor profile buckets are (kind × array): want_tags carries
    # position/skill/topic; have_tags carries skill/topic. Intent is
    # implicit in *which* array a subject_group lives in — no separate
    # enum needed.
    SKILL = 'skill'
    POSITION = 'position'
    TOPIC = 'topic'
