from types import coroutine
from typing import Any, Optional, Type

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


# model 跟 model 互轉的方法們，如果有特別需求請override


def convert_dto_to_model(dto: BaseModel, model_class: Any, exclude: set = {}):
    # 僅處理同名key/value
    # exclude代表有些值不存在於dto/model中 需手動決定要怎麼處理
    return model_class(**dto.dict(exclude=exclude))


async def get_all_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    query = await db.execute(stmt)
    res: coroutine = query.scalars().all()
    return res

async def fetch_all_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    query = await db.execute(stmt)
    res: coroutine = query.fetchall()
    return res


async def get_first_template(db: AsyncSession, stmt: Select) -> Optional[Any]:
    result = await db.execute(stmt)
    res: coroutine = result.scalars().first()
    return res
