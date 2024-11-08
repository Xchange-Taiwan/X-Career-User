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
        return [self.convert_profile_to_dto(profile) for profile in profiles]

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)

        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        return self.convert_profile_to_dto(query)

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
        return [self.convert_profile_to_dto(profile) for profile in profiles]

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileDTO:
        model = convert_dto_to_model(dto, Profile)

        if model.user_id is None or model.user_id == '':
            # New entity, do auto increment
            # Refresh the model when it an insert
            db.add(model)
            await db.commit()
            # Refresh the model when it an insert
            await db.refresh(model)
        else:
            # Check if the record exists
            query = select(Profile).filter_by(user_id=model.user_id)
            result = await db.execute(query)

            existing_model = result.scalars().first()

            if existing_model is not None:
                # Update the existing model
                for key, value in model.__dict__.items():
                    if key != "_sa_instance_state":
                        setattr(existing_model, key, value)
                await db.merge(existing_model)
                await db.commit()
            else:
                # Insert the new model
                db.add(model)
                await db.commit()
                # Refresh the model when it an insert
                await db.refresh(model)

        return self.convert_profile_to_dto(model)

    async def delete_profile(self, db: AsyncSession, user_id: str) -> None:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        mentor = get_first_template(db, stmt)
        if mentor:
            await db.delete(mentor)
            await db.commit()

    def convert_dto_to_profile(self, dto: ProfileDTO) -> Profile:
        profile: Profile = Profile()
        profile.user_id = dto.user_id
        profile.name = dto.name
        profile.avatar = dto.avatar
        profile.timezone = dto.timezone
        profile.industry = dto.industry
        profile.position = dto.position
        profile.company = dto.company
        profile.linkedin_profile = dto.linkedin_profile
        profile.interested_positions = dto.interested_positions
        profile.skills = dto.skills
        profile.topics = dto.topics
        return profile

    def convert_profile_to_dto(self, model: Profile) -> ProfileDTO:
        profile_dto: ProfileDTO = ProfileDTO()
        profile_dto.user_id = model.user_id
        profile_dto.name = model.name
        profile_dto.avatar = model.avatar
        profile_dto.timezone = model.timezone
        profile_dto.industry = model.industry
        profile_dto.position = model.position
        profile_dto.company = model.company
        profile_dto.linkedin_profile = model.linkedin_profile
        profile_dto.interested_positions = model.interested_positions
        profile_dto.skills = model.skills
        profile_dto.topics = model.topics
        return profile_dto
