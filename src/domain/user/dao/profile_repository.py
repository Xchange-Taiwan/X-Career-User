from typing import Optional

from sqlalchemy import select, Select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.user.model.user_model import ProfileDTO
from src.infra.db.orm.init.user_init import Profile
from src.infra.util.convert_util import get_first_template


class ProfileRepository:

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)

        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        return ProfileDTO.model_validate(query)

    async def find_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[ProfileDTO]:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            return None
        return ProfileDTO.model_validate(query)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileDTO:
        if (dto is None) or (dto.user_id is None):
            raise NotFoundException(msg="not a valid user")

        # Load-or-create instead of db.merge — ProfileDTO no longer covers
        # every Profile column (mentor-only want_tags/have_tags live on the
        # row but not the mentee dto), and merge would copy unset attrs as
        # NULL, clobbering existing tag arrays.
        existing: Optional[Profile] = await db.get(Profile, dto.user_id)
        if existing is None:
            model = Profile(**dto.model_dump())
            db.add(model)
            await db.commit()
            await db.refresh(model)
            return ProfileDTO.model_validate(model)

        for key, value in dto.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return ProfileDTO.model_validate(existing)

    async def delete_profile(self, db: AsyncSession, user_id: int) -> None:
        stmt = sa_delete(Profile).where(Profile.user_id == user_id)
        await db.execute(stmt)
