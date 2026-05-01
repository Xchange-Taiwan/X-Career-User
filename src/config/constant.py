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
    # Two intent axes share the same kind:
    #   skill   — WANT (mentee wants to learn) or OFFER (mentor can teach)
    #   topic   — WANT (mentee wants to discuss) or OFFER (mentor can mentor on)
    #   position — WANT (mentee interested in this role)
    # `expertise` and `what_i_offer` were collapsed into `skill` / `topic`
    # respectively under the two-layer redesign — intent flag does the work.
    SKILL = 'skill'
    POSITION = 'position'
    TOPIC = 'topic'


class TagIntent(Enum):
    WANT = 'WANT'
    OFFER = 'OFFER'
