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

    async def get_mentor_profiles_by_conditions(self, db: AsyncSession, dto: MentorProfileDTO) -> List[
        MentorProfileDTO]:
        # Convert DTO to dictionary for dynamic filtering
        dto_dict = {key: value for key, value in dto.__dict__.items() if value is not None}

        # Base query
        query = select(Profile)

        # Simple equality filters
        filters = {
            'name': Profile.name,
            'language': Profile.language,
            'seniority_level': Profile.seniority_level,
            'industry': Profile.industry,
            'job_title': Profile.job_title,
            'company': Profile.company,
            'experience': Profile.experience
        }
        for field, column in filters.items():
            if field in dto_dict:
                query = query.filter(column == dto_dict[field])

        # JSON array fields with 'any' filtering
        jsonb_filters = {
            'skills': Profile.skills,
            'topics': Profile.topics,
            'expertises': Profile.expertises
        }
        for field, column in jsonb_filters.items():
            if field in dto_dict:
                query = query.filter(
                    func.cast(func.jsonb_array_elements_text(column), Integer).any_(dto_dict[field])
                )

        # Execute query and convert results to DTOs
        profiles = await get_all_template(db, query)
        return [convert_model_to_dto(profile, MentorProfileDTO) for profile in profiles]

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        model: Profile = convert_dto_to_model(mentor_profile_dto, Profile)
        if model.user_id is None or model.user_id == '':
            # New entity, do auto increment
            # Refresh the model when it an insert
            db.add(model)
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

            else:
                # Insert the new model
                db.add(model)
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
        profile_dto.position = model.job_title
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
