from typing import List

from sqlalchemy import func, Integer, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.domain.user.dao.profile_repository import assign_avatar_updated_at
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import (
    get_first_template,
    get_all_template,
    convert_dto_to_model,
)


class MentorRepository:

    async def get_mentor_profile_by_id(self, db: AsyncSession, mentor_id: int) -> MentorProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id)
        mentor: Profile = await get_first_template(db, stmt)
        # join MentorExperience 有存在的才返回
        return MentorProfileDTO.model_validate(mentor)

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        await assign_avatar_updated_at(db, mentor_profile_dto)
        model: Profile = convert_dto_to_model(mentor_profile_dto, Profile)

        model = await db.merge(model)
        res: MentorProfileDTO = MentorProfileDTO.model_validate(model)
        await db.commit()
        return res

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()
