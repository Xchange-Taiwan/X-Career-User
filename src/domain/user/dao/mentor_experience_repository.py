from typing import List
from sqlalchemy import Select, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.config.exception import NotFoundException
from src.domain.mentor.model.experience_model import ExperienceDTO
from src.infra.db.orm.init.user_init import MentorExperience, Profile
from src.infra.util.convert_util import get_first_template, get_all_template


class MentorExperienceRepository:
    async def upsert_mentor_exp_by_user_id(self, db: AsyncSession, 
                                           user_id: int,
                                           mentor_exp_dto: ExperienceDTO,
                                          ) -> MentorExperience:
        mentor_exp: MentorExperience = MentorExperience(id=mentor_exp_dto.id,
                                                        user_id=user_id,
                                                        category=mentor_exp_dto.category,
                                                        order=mentor_exp_dto.order,
                                                        mentor_experiences_metadata = mentor_exp_dto.mentor_experiences_metadata
                                                        )

        mentor_exp = await db.merge(mentor_exp)
        await db.commit()
        await db.refresh(mentor_exp)

        return mentor_exp

    async def get_mentor_exp_by_id(self, db: AsyncSession, exp_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.id == exp_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    # NOTE: 育志，這個函數應該要回傳多個經驗，而不是一個；多個經驗應該要是一個列表複製到 Elasticsearch 的資料庫
    async def get_mentor_exp_list_by_user_id(self, db: AsyncSession, user_id: int) -> List[MentorExperience]:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_exp: MentorExperience = await get_all_template(db, stmt)

        return mentor_exp

    async def get_mentor_exp_by_user_id(self, db: AsyncSession, user_id: int) -> MentorExperience:
        stmt: Select = select(MentorExperience).filter(MentorExperience.user_id == user_id)
        mentor_exp: MentorExperience = await get_first_template(db, stmt)

        return mentor_exp

    async def delete_mentor_exp_by_id(self, db: AsyncSession, 
                                      user_id: int, 
                                      experience_dto: ExperienceDTO) -> bool:
        exp_id = experience_dto.id
        exp_cate = experience_dto.category
        stmt: Select = \
            select(MentorExperience).where(and_(
                                                MentorExperience.user_id == user_id,
                                                MentorExperience.id == exp_id,
                                                MentorExperience.category == exp_cate,
                                            )
                                        )
                        
        mentor_exp: MentorExperience = await get_first_template(db, stmt)
        if mentor_exp is not None:
            await db.delete(mentor_exp)
            await db.commit()
            return True

        return False

