from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.config.exception import NotFoundException
from src.domain.mentor.model.experience_model import ExperienceDTO
from src.infra.db.orm.init.user_init import MentorExperience, Profile
from src.infra.util.convert_util import get_first_template


class MentorExperienceRepository:
    async def upsert_mentor_exp_by_user_id(self, db: AsyncSession, mentor_exp_dto: ExperienceDTO,
                                           user_id: int, exp_cate: ExperienceCategory) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)
        mentor: Profile = await get_first_template(db, mentor_stmt)
        if mentor_exp is None:
            mentor_exp = MentorExperience()
            mentor_exp.user_id = user_id
            mentor_exp.order = mentor_exp_dto.order
            mentor_exp.category = exp_cate
            mentor_exp.desc = mentor_exp_dto.desc

        else:
            mentor_exp.order = mentor_exp_dto.order
            mentor_exp.category = exp_cate
            mentor_exp.desc = mentor_exp_dto.desc
        await db.merge(mentor_exp)
        mentor.experience = mentor_exp.id

        return mentor_exp

    async def get_mentor_exp_by_id(self, db: AsyncSession, exp_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.id == exp_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    async def get_mentor_exp_by_user_id(self, db: AsyncSession, user_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    async def delete_mentor_exp_by_id(self, db: AsyncSession, user_id: int, exp_id: int, exp_cate: ExperienceCategory) -> None:
        stmt: Select = (
            select(MentorExperience).filter(MentorExperience.user_id == user_id
                                            and MentorExperience.id == exp_id) and MentorExperience.category == exp_cate)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)
        # mentor_stmt: Select = select(Profile).filter(Profile.user_id == mentor_exp.user_id)
        # mentor: Profile = await get_first_template(db, mentor_stmt)
        # mentor.experience = None
        if mentor_exp is not None:
            await db.delete(mentor_exp)

        else:
            raise NotFoundException(msg=f"No such experience with id: {exp_id}")

