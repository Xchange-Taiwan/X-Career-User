from enum import Enum


class SeniorityLevel(Enum):
    NO_REVEAL = 'no reveal'
    JUNIOR = 'junior'
    INTERMEDIATE = 'intermediate'
    SENIOR = 'senior'
    STAFF = 'staff'
    MANAGER = 'manager'


class ScheduleType(Enum):
    ALLOW = 'allow'
    FORBIDDEN = 'forbidden'
