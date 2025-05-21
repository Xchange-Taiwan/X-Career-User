from typing import Optional

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.user.model.user_model import ProfileDTO
from src.infra.db.orm.init.user_init import Profile
from src.infra.util.convert_util import convert_dto_to_model, get_first_template


class ProfileRepository:

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)

        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        return ProfileDTO.model_validate(query)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileDTO:
        if (dto is None) or (dto.user_id is None):
            raise NotFoundException(msg="not a valid user")
        # directly upsert since the user_id should be pre dedined in auth service

        model: Profile = convert_dto_to_model(dto, Profile)
        model = await db.merge(model)

        await db.commit()
        await db.refresh(model)
        return ProfileDTO.model_validate(model)

    async def delete_profile(self, db: AsyncSession, user_id: str) -> None:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        mentor = get_first_template(db, stmt)
        if mentor:
            await db.delete(mentor)
            await db.commit()

