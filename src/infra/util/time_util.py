import time
from datetime import datetime
from typing import Optional

import recurring_ical_events
from icalendar import Calendar, Event


def shift_decimal(number, places):
    return number * (10 ** places)


def gen_timestamp():
    return int(shift_decimal(time.time(), 3))


def str_to_timestamp(datetime_str: str, date_format: str):
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+0000'
    dt = datetime.strptime(datetime_str, date_format)
    return int(dt.timestamp())


def current_seconds():
    return int(time.time())


################################
# iCanlendar transfer utils
################################

# parse rrule string to dict
def get_rrule_dict(rrule: str, date_format: str):
    rrule_dict = {}
    for item in rrule.split(';'):
        key, value = item.split('=')
        if key == 'UNTIL':
            value = datetime.strptime(value, date_format)
        elif ',' in value:
            value = value.split(',')
        rrule_dict[key] = value
    return rrule_dict


# create a iCalendar event with recurring event
def create_calendar_with_rrule(event_title: str,
                               start_date: datetime,
                               end_date: datetime,
                               dt_format: str,
                               rrule: Optional[str] = None):
    cal = Calendar()
    event = Event()
    event.add('summary', event_title)  # event title
    event.add('dtstart', start_date)  # start time
    event.add('dtend', end_date)  # end time
    if rrule:
        rrule_dict = get_rrule_dict(rrule, dt_format) # 合法的 rrule_dict
        event.add('rrule', rrule_dict)
    cal.add_component(event)
    return cal


# NOTE: recurring_ical_events 不直接引用，皆透過 time_util.py 進行引用
# 處理日期/時間的工具皆引用自 time_util.py, 不依賴特定模組/libs
def rrule_events(cal: Calendar, start_date: datetime, end_date: datetime):
    return recurring_ical_events.of(cal).between(start_date, end_date)
