from enum import Enum


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


class ScheduleType(Enum):
    ALLOW = 'ALLOW'
    FORBIDDEN = 'FORBIDDEN'


class RoleType(Enum):
    MENTOR = 'MENTOR'
    MENTEE = 'MENTEE'


class BookingStatus(Enum):
    PENDING = 'PENDING'
    ACCEPT = 'ACCEPT'
    REJECT = 'REJECT'


class ReservationListState(Enum):
    UPCOMING = 'UPCOMING'
    PENDING = 'PENDING'
    HISTORY = 'HISTORY'


class SortingBy(Enum):
    UPDATED_TIME = 'UPDATED_TIME'
    # VIEW = 'view'


class Sorting(Enum):
    ASC = 1
    DESC = -1


class SchedulesType(Enum):
    ALLOW = "ALLOW"
    FORBIDDEN = "FORBIDDEN"
