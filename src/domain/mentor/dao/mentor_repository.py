from typing import List

from sqlalchemy import func, Integer, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import get_first_template, get_all_template


class MentorRepository:

    async def get_all_mentor_profile(self, db: AsyncSession) -> List[MentorProfileDTO]:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        mentors: List[Profile] = await get_all_template(db, stmt)
        return [Profile.to_mentor_profile_dto(mentor) for mentor in mentors]

    async def get_mentor_profile_by_id_and_language(self, db: AsyncSession, mentor_id: int,
                                                    language: str) -> MentorProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id, Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)
        # join MentorExperience 有存在的才返回
        return Profile.to_mentor_profile_dto(mentor)

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
        profiles: List[Profile] = await get_all_template(db, query)
        return [Profile.to_mentor_profile_dto(mentor) for mentor in profiles]

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        model: Profile = Profile.of_mentor_profile(mentor_profile_dto)

        await db.merge(model)
        res: MentorProfileDTO = Profile.to_mentor_profile_dto(model)

        return res

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
