from fastapi import Request, Path, Body
from typing import Dict, List
from src.config.exception import ClientException
from src.domain.mentor.model.mentor_model import TimeSlotDTO



def upsert_mentor_schedule_check(
    user_id: int = Path(...),
    body: List[TimeSlotDTO] = Body(...),
) -> (List[TimeSlotDTO]):
    if body is None or not body:
        raise ClientException(msg='Prepare your data')

    for timeslot in body:
        if timeslot.dtstart >= timeslot.dtend:
            raise ClientException(msg='dtstart should smaller then dtend')
    # TODO: 儲存前檢查用戶的時間是否衝突? 若有則拋錯 (等有人開始用 反饋了再優化)
    # 這裡僅檢查用戶輸入資料的衝突

    # initial fields
    body = [timeslot.init_fields(user_id) for timeslot in body]
    return body
