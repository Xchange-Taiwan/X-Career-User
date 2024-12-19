from types import coroutine
from typing import Any, Optional, Type, Dict
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.conf import DATETIME_FORMAT


# model 跟 model 互轉的方法們，如果有特別需求請override


def convert_dto_to_model(dto: BaseModel, model_class: Any, exclude: set = {}):
    # 僅處理同名key/value
    # exclude代表有些值不存在於dto/model中 需手動決定要怎麼處理
    return model_class(**dto.dict(exclude=exclude))


async def get_all_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    query = await db.execute(stmt)
    res: coroutine = query.scalars().all()
    return res


async def get_first_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    result = await db.execute(stmt)
    res: coroutine = result.scalars().first()
    return res


'''
只能轉換至多第2層的欄位，如果有複雜的欄位結構，請自行處理
'''
def json_encoders(base_model: BaseModel, datetime_format: str = DATETIME_FORMAT) -> Dict:
    # 訪問每個欄位並取得資料型態
    model_json: Dict = {}
    for field_name, field in base_model.__fields__.items():
        field_type = field.type_
        field_value = getattr(base_model, field_name)
        
        # 根據型態進行轉換
        # datetime型態轉換成字串
        if field_type is datetime:
            if isinstance(field_value, list):
                model_json[field_name] = [value.strftime(datetime_format) for value in field_value]
            else:
                model_json[field_name] = field_value.strftime(datetime_format)
            continue
        
        # TODO: XXXX型態轉換成字串
            
        model_json[field_name] = field_value
        
    return model_json
