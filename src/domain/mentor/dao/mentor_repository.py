from typing import List

from sqlalchemy import func, Integer, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import convert_model_to_dto, convert_dto_to_model, get_first_template, get_all_template


class MentorRepository:

    async def get_all_mentor_profile(self, db: AsyncSession) -> List[MentorProfileDTO]:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        mentors: List[Profile] = await get_all_template(db, stmt)
        return [convert_model_to_dto(mentor, MentorProfileDTO) for mentor in mentors]

    async def get_mentor_profile_by_id_and_language(self, db: AsyncSession, mentor_id: int,
                                                    language: str) -> MentorProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id, Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)
        # join MentorExperience 有存在的才返回
        return self.convert_mentor_profile_to_dto(mentor)

    async def get_mentor_profiles_by_conditions(self, db: AsyncSession, dto: MentorProfileDTO) \
            -> List[MentorProfileDTO]:
        dto_dict = dict(dto.__dict__)

        query: Select = select(Profile)
        if dto_dict.get('name') is not None:
            query = query.filter(Profile.name == dto.name)
        if dto_dict.get('language') is not None:
            query = query.filter(Profile.language == dto.language)
        if dto_dict.get('location') is not None:
            query = query.filter(Profile.location.like('%' + dto.location + '%'))
        if dto_dict.get('about') is not None:
            query = query.filter(Profile.about.like('%' + dto.about + '%'))
        if dto_dict.get('personal_statement') is not None:
            query = query.filter(Profile.about.like('%' + dto.personal_statement + '%'))
        if dto_dict.get('seniority_level') is not None:
            query = query.filter(Profile.seniority_level == dto.seniority_level)
        if dto_dict.get('industry') is not None:
            query = query.filter(Profile.industry == dto.industry)
        if dto_dict.get('position') is not None:
            query = query.filter(Profile.position == dto.position)
        if dto_dict.get('company') is not None:
            query = query.filter(Profile.company == dto.company)
        if dto_dict.get('experience') is not None:
            query = query.filter(Profile.experience >= dto.experience)

        if dto_dict.get('skills') is not None:
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.skills), Integer).any_(dto.skills)
            )
        if dto_dict.get('topics') is not None:
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.topics), Integer).any_(dto.topics)
            )
        if dto_dict.get('expertises') is not None:
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.expertises), Integer).any_(dto.expertises)
            )
        profiles = await get_all_template(db, query)
        return [convert_model_to_dto(profile, MentorProfileDTO) for profile in profiles]

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        model: Profile = convert_dto_to_model(mentor_profile_dto, Profile)
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
        res: MentorProfileDTO = convert_model_to_dto(model, MentorProfileDTO)

        return res

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()

    def convert_mentor_profile_to_dto(self, model: Profile) -> MentorProfileDTO:
        profile_dto: MentorProfileDTO = MentorProfileDTO()
        if model is None:
            return profile_dto
        profile_dto.user_id = model.user_id
        profile_dto.language = model.language
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
        profile_dto.seniority_level = model.seniority_level
        profile_dto.location = model.location
        profile_dto.about = model.about
        profile_dto.experience = model.experience
        profile_dto.expertises = model.expertises
        profile_dto.personal_statement = model.personal_statement
        return profile_dto
