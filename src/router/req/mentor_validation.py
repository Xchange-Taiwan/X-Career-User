import sys
from fastapi import Request, Path, Body
from typing import Dict, List
from src.config.exception import ClientException
from src.config.conf import (
    BATCH,
    MAX_PERIOD_SECS,
)
from src.domain.mentor.model.mentor_model import TimeSlotDTO


def upsert_mentor_schedule_check(
    user_id: int = Path(...),
    timeslot_dtos: List[TimeSlotDTO] = Body(...),
) -> (List[TimeSlotDTO]):
    # CHECK: 資料筆數不可為空
    if timeslot_dtos is None or not timeslot_dtos:
        raise ClientException(msg='Prepare your data')

    # CHECK: 每次新增/更新資料筆數不可大於 BATCH
    timeslots_length = len(timeslot_dtos)
    if timeslots_length > BATCH:
        raise ClientException(msg=f'The number of timeslots shouldn\'t over {BATCH}')


    # 初始化欄位
    timeslot_dtos = [timeslot.init_fields(user_id) for timeslot in timeslot_dtos]


    # CHECK: 開始時間(dtstart)應小於結束時間(dtend)
    for timeslot in timeslot_dtos:
        if timeslot.dtstart >= timeslot.dtend:
            raise ClientException(msg=f'dtstart:{timeslot.dtstart} should smaller then dtend:{timeslot.dtend}')


    # CHECK: 所有的時間區間中，最早(dtstart)和最晚(dtend)時間區間相差不超過 MAX_PERIOD
    (min_dtstart, max_dtend) = TimeSlotDTO.min_dtstart_and_max_dtend(timeslot_dtos)
    if max_dtend - min_dtstart > MAX_PERIOD_SECS:
        raise ClientException(msg=f'The max time period shouldn\'t over {MAX_PERIOD_SECS / 86400} days')


    # CHECK: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (這裡僅比對用戶的輸入資料)
    if timeslots_length > 1:
        TimeSlotDTO.datetime_conflict_check(timeslot_dtos)


    return timeslot_dtos
