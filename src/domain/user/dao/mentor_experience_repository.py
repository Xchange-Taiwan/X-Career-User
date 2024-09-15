from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.domain.mentor.model.experience_model import ExperienceDTO
from src.infra.db.orm.init.user_init import MentorExperience
from src.infra.util.convert_util import get_first_template


class MentorExperienceRepository:
    async def upsert_mentor_exp_by_user_id(self, db: AsyncSession, mentor_exp_dto: ExperienceDTO,
                                           user_id: int, exp_cate: ExperienceCategory) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        if mentor_exp is None:
            mentor_exp = MentorExperience()
            mentor_exp.user_id = user_id
            mentor_exp.order = mentor_exp_dto.order
            mentor_exp.category = exp_cate
            mentor_exp.language = mentor_exp_dto.language
            mentor_exp.desc = mentor_exp_dto.desc
            db.add(mentor_exp)

        else:
            mentor_exp.order = mentor_exp_dto.order
            mentor_exp.category = exp_cate
            mentor_exp.language = mentor_exp_dto.language
            mentor_exp.desc = mentor_exp_dto.desc
            await db.merge(mentor_exp)
        await db.commit()
        await db.refresh(mentor_exp)  # commit後要重讀一次db 不然會沒有值

        return mentor_exp

    async def get_mentor_exp_by_id(self, db: AsyncSession, exp_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.id == exp_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    async def get_mentor_exp_by_user_id(self, db: AsyncSession, user_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    async def delete_mentor_exp_by_id(self, db: AsyncSession, user_id: int, language: str) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id,
                                                       MentorExperience.language == language)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)
        if mentor_exp is not None:
            await db.delete(mentor_exp)
            await db.commit()
        return mentor_exp

    def convert_exp_to_dto(self, model: MentorExperience):
        res: ExperienceDTO = ExperienceDTO()
        res.user_id = model.id
        res.category = model.category
        res.order = model.order
        res.desc = model.desc
        return res
