from typing import List

from sqlalchemy import func, Integer, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import get_first_template, get_all_template


class MentorRepository:

    async def get_mentor_profile_by_id_and_language(self, db: AsyncSession, mentor_id: int,
                                                    language: str) -> MentorProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id, Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)
        # join MentorExperience 有存在的才返回
        return Profile.to_mentor_profile_dto(mentor)


    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        model: Profile = Profile.of_mentor_profile(mentor_profile_dto)

        model = await db.merge(model)
        await db.commit()

        res: MentorProfileDTO = Profile.to_mentor_profile_dto(model)

        return res

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()
