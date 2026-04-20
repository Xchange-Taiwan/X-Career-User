import time
from datetime import datetime, timezone as _tz
from typing import List, Optional, Tuple

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


################################
# Schedule occurrence utils
################################

def month_range_ts(dt_year: int, dt_month: int) -> Tuple[int, int]:
    # 以 UTC 為基準回傳 [月初, 次月初) 的 epoch 秒數區間
    start = datetime(dt_year, dt_month, 1, tzinfo=_tz.utc)
    if dt_month == 12:
        end = datetime(dt_year + 1, 1, 1, tzinfo=_tz.utc)
    else:
        end = datetime(dt_year, dt_month + 1, 1, tzinfo=_tz.utc)
    return int(start.timestamp()), int(end.timestamp())


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    # 閉開區間 [start, end) 的重疊判定，邊界相接不算衝突
    return a_start < b_end and b_start < a_end


def expand_occurrences(
    dtstart: int,
    dtend: int,
    rrule: Optional[str],
    exdate: Optional[List[int]],
    dt_format: str,
    window_start: int,
    window_end: int,
) -> List[Tuple[int, int]]:
    # 將單一 schedule 展開成落在 [window_start, window_end) 內的 (dtstart, dtend) occurrence 列表
    # - 無 rrule 時只會回傳至多一筆（與視窗重疊者）
    # - 有 rrule 時透過 recurring_ical_events 展開，並以 exdate 剔除例外點
    exdate_set = set(int(x) for x in (exdate or []))

    if not rrule:
        if exdate_set and int(dtstart) in exdate_set:
            return []
        if overlaps(int(dtstart), int(dtend), window_start, window_end):
            return [(int(dtstart), int(dtend))]
        return []

    start_date = datetime.fromtimestamp(int(dtstart))
    end_date = datetime.fromtimestamp(int(dtend))
    cal = create_calendar_with_rrule(
        event_title='SCHEDULE',
        start_date=start_date,
        end_date=end_date,
        dt_format=dt_format,
        rrule=rrule,
    )

    window_start_dt = datetime.fromtimestamp(window_start)
    window_end_dt = datetime.fromtimestamp(window_end)
    events = rrule_events(cal, window_start_dt, window_end_dt)

    occurrences: List[Tuple[int, int]] = []
    for event in events:
        occ_start = int(event.get('DTSTART').dt.timestamp())
        occ_end = int(event.get('DTEND').dt.timestamp())
        if occ_start in exdate_set:
            continue
        if not overlaps(occ_start, occ_end, window_start, window_end):
            continue
        occurrences.append((occ_start, occ_end))
    return occurrences
