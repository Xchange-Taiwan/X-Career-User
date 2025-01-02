import sys
from fastapi import Request, Path, Body
from typing import Dict, List
from src.config.exception import ClientException
from src.config.conf import (
    BATCH,
    MAX_PERIOD_SECS,
)
from src.domain.mentor.model.mentor_model import MentorScheduleDTO


def upsert_mentor_schedule_check(
    user_id: int = Path(...),
    schedule_dto: MentorScheduleDTO = Body(...),
) -> (MentorScheduleDTO):
    
    timeslots = schedule_dto.timeslots

    # CHECK: 資料筆數不可為空
    if timeslots is None or not timeslots:
        raise ClientException(msg='Prepare your data')

    # CHECK: 每次新增/更新資料筆數不可大於 BATCH
    timeslots_length = len(timeslots)
    if timeslots_length > BATCH:
        raise ClientException(msg=f'The number of timeslots shouldn\'t over {BATCH}')

    # 初始化欄位
    schedule_dto.timeslots = timeslots = [timeslot.init_fields(user_id) for timeslot in timeslots]

    # CHECK: 開始時間(dtstart)應小於結束時間(dtend)
    for timeslot in timeslots:
        if timeslot.dtstart >= timeslot.dtend:
            raise ClientException(msg=f'dtstart:{timeslot.dtstart} should smaller then dtend:{timeslot.dtend}')

    # CHECK: 所有"事件"的時間區間中(不展開 rrule)，最早(dtstart)和最晚(dtend)時間區間相差不超過 MAX_PERIOD
    (min_dtstart, max_dtend) = schedule_dto.min_dtstart_to_max_dtend()
    if max_dtend - min_dtstart > MAX_PERIOD_SECS:
        raise ClientException(msg=f'The max time period shouldn\'t over {MAX_PERIOD_SECS / 86400} days')

    # CHECK: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (這裡僅比對用戶的輸入資料)
    if timeslots_length > 1:
        MentorScheduleDTO.opverlapping_interval_check(timeslots, schedule_dto.until)

    return schedule_dto
