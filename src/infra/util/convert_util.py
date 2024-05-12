from types import coroutine
from typing import Any, List, Optional

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query


# model 跟 model 互轉的方法們，如果有特別需求請override
def convert_model_to_dto(model_class: Any, dto_class: BaseModel):
    return dto_class.parse_obj(dict(model_class.__dict__))


def convert_dto_to_model(dto: BaseModel, model_class: Any, exclude: set = {}):
    #僅處理同名key/value
    #exclude代表有些值不存在於dto/model中 需手動決定要怎麼處理
    return model_class(**dto.dict(exclude=exclude))


async def get_all_template(db: AsyncSession, stmt: Select) -> List[Any]:
    query = await db.execute(stmt)
    res: coroutine = query.scalars().all()
    return res


async def get_first_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    result = await db.execute(stmt)
    res: coroutine = result.scalars().first()
    return res
