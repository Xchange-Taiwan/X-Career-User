from typing import List

from sqlalchemy import func, Integer, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import convert_model_to_dto, convert_dto_to_model, get_first_template, get_all_template


class MentorRepository:

    def __init__(self):
        self.stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
    async def get_all_mentor_profile(self, db: AsyncSession) -> List[MentorProfileDTO]:
        stmt: Select = self.stmt
        mentors: List[Profile] = await get_all_template(db, stmt)
        return [convert_model_to_dto(mentor, MentorProfileDTO) for mentor in mentors]

    async def get_mentor_profile_by_id(self, db: AsyncSession, mentor_id: int) -> MentorProfileDTO:

        stmt: Select = self.stmt.filter(Profile.user_id == mentor_id)
        mentor: Profile = await get_first_template(db, stmt)
        # join MentorExperience 有存在的才返回
        return self.convert_mentor_profile_to_dto(mentor)

    async def get_mentor_profiles_by_conditions(self, db: AsyncSession, dto: MentorProfileDTO) -> List[
        MentorProfileDTO]:
        dto_dict = dict(dto.__dict__)
        query = db.query(Profile)
        if dto_dict.get('name'):
            query = query.filter(Profile.name == dto.name)
        if dto_dict.get('location'):
            query = query.filter(Profile.location.like('%' + dto.location + '%'))
        if dto_dict.get('about'):
            query = query.filter(Profile.about.like('%' + dto.about + '%'))
        if dto_dict.get('personal_statement'):
            query = query.filter(Profile.about.like('%' + dto.personal_statement + '%'))
        if dto_dict.get('seniority_level'):
            query = query.filter(Profile.seniority_level == dto.seniority_level)
        if dto_dict.get('industry'):
            query = query.filter(Profile.industry == dto.industry)
        if dto_dict.get('position'):
            query = query.filter(Profile.position == dto.position)
        if dto_dict.get('company'):
            query = query.filter(Profile.company == dto.company)
        if dto_dict.get('experience'):
            query = query.filter(Profile.experience >= dto.experience)

        if dto_dict.get('skills'):
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.skills), Integer).any_(dto.skills)
            )
        if dto_dict.get('topics'):
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.topics), Integer).any_(dto.topics)
            )
        if dto_dict.get('expertises'):
            query = query.filter(
                func.cast(func.jsonb_array_elements_text(Profile.expertises), Integer).any_(dto.expertises)
            )
        profiles = await query.all()
        return [convert_model_to_dto(profile, MentorProfileDTO) for profile in profiles]

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        mentor = convert_dto_to_model(mentor_profile_dto, Profile)
        await db.merge(mentor)
        res = convert_model_to_dto(mentor, MentorProfileDTO)

        return res

    async def delete_mentor_profile_by_id(self, db: AsyncSession, user_id: int) -> None:
        stmt: Select = self.stmt.filter(Profile.user_id == user_id)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()

    def convert_mentor_profile_to_dto(self, model: Profile) -> MentorProfileDTO:
        profile_dto: MentorProfileDTO = MentorProfileDTO()
        if (model is None):
            return profile_dto
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
        profile_dto.seniority_level = model.seniority_level
        profile_dto.location = model.location
        profile_dto.about = model.about
        profile_dto.experience = model.experience
        profile_dto.expertises = model.expertises
        return profile_dto
