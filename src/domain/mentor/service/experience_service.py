from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.config.exception import NotFoundException
from src.domain.mentor.model.experience_model import ExperienceVO, ExperienceDTO
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.infra.db.orm.init.user_init import MentorExperience


class ExperienceService:
    def __init__(self, exp_dao: MentorExperienceRepository):
        self.__exp_dao = exp_dao

    async def get_exp_by_exp_id_and_language(self, db: AsyncSession, exp_id: int, language: str) -> ExperienceVO:
        mentor_exp: MentorExperience = await self.__exp_dao.get_mentor_exp_by_id(db, exp_id)
        return ExperienceVO.of(mentor_exp)

    async def get_exp_by_user_id(self, db: AsyncSession, user_id: int, language: str) -> ExperienceVO:
        mentor_exp: MentorExperience = await self.__exp_dao.get_mentor_exp_by_user_id(db, user_id)
        return ExperienceVO.of(mentor_exp)

    async def upsert_exp(self, db: AsyncSession, experience_dto: ExperienceDTO, user_id: int,
                         exp_cate: ExperienceCategory) -> ExperienceVO:
        mentor_exp: MentorExperience = await self.__exp_dao.upsert_mentor_exp_by_user_id(db=db,
                                                                                         mentor_exp_dto=experience_dto,
                                                                                         user_id=user_id,
                                                                                         exp_cate=exp_cate)
        res: ExperienceVO = ExperienceVO.of(mentor_exp)

        return res

    async def delete_exp_by_id(self, db: AsyncSession, user_id: int) -> bool:
        try:
            await self.__exp_dao.delete_mentor_exp_by_id(db, user_id)
            return True
        except NotFoundException:
            return False

