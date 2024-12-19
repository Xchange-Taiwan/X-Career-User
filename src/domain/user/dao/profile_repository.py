from typing import List, Optional, Type

from sqlalchemy import func, Integer, select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.user.model.user_model import ProfileDTO
from src.infra.db.orm.init.user_init import Profile
from src.infra.util.convert_util import convert_dto_to_model, get_all_template, get_first_template


class ProfileRepository:

    async def get_all_profile(self, db: AsyncSession) -> List[ProfileDTO]:
        stmt: Select = select(Profile)
        profiles: List[Type[Profile]] = await get_all_template(db, stmt)
        return [Profile.to_dto(profile) for profile in profiles]

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)

        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        return Profile.to_dto(query)

    async def get_profiles_by_conditions(self, db: AsyncSession, dto: ProfileDTO) -> List[ProfileDTO]:
        dto_dict = dict(dto.__dict__)
        query: Select = select(Profile)

        if dto_dict.get('name'):
            query = query.filter(Profile.name.like('%' + dto.name + '%'))

        if dto_dict.get('skills'):
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.skills), Integer).any_(dto.skills)
            )
        if dto_dict.get('topics'):
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.topics), Integer).any_(dto.topics)
            )
        profiles = await get_all_template(db, query)
        return [Profile.to_dto(profile) for profile in profiles]

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileDTO:
        model: Profile = convert_dto_to_model(dto, Profile)

        # Check if the record exists
        query = select(Profile).filter_by(user_id=model.user_id)
        result = await db.execute(query)

        existing_model = result.scalars().first()

        if existing_model is not None:
            # Update the existing model
            for key, value in model.__dict__.items():
                if key != "_sa_instance_state":
                    setattr(existing_model, key, value)

        model = await db.merge(model)

        await db.commit()
        await db.refresh(model)
        return Profile.to_dto(model)

    async def delete_profile(self, db: AsyncSession, user_id: str) -> None:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        mentor = get_first_template(db, stmt)
        if mentor:
            await db.delete(mentor)

