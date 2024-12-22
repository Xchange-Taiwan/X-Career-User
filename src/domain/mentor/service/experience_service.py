from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.config.exception import NotFoundException, ServerException
from src.domain.mentor.model.experience_model import ExperienceVO, ExperienceDTO
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.infra.db.orm.init.user_init import MentorExperience
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ExperienceService:
    def __init__(self, exp_dao: MentorExperienceRepository):
        self.__exp_dao = exp_dao

    async def get_exp_by_user_id(self, db: AsyncSession, user_id: int) -> ExperienceVO:
        try:
            mentor_exp: MentorExperience = await self.__exp_dao.get_mentor_exp_by_user_id(db, user_id)
            return ExperienceVO.of(mentor_exp)
        except Exception as e:
            log.error(f'get_exp_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience response failed')

    async def upsert_exp(self, db: AsyncSession, experience_dto: ExperienceDTO, user_id: int,
                         exp_cate: ExperienceCategory) -> ExperienceVO:
        try:
            mentor_exp: MentorExperience = await self.__exp_dao.upsert_mentor_exp_by_user_id(db=db,
                                                                                            mentor_exp_dto=experience_dto,
                                                                                            user_id=user_id,
                                                                                            exp_cate=exp_cate)
            res: ExperienceVO = ExperienceVO.of(mentor_exp)

            return res
        except Exception as e:
            log.error(f'upsert_exp error: %s', str(e))
            raise ServerException(msg='upsert experience response failed')

    async def delete_exp_by_user_and_exp_id(self, db: AsyncSession, user_id: int, exp_id: int, exp_cate: ExperienceCategory) -> bool:
        try:
            await self.__exp_dao.delete_mentor_exp_by_id(db, user_id, exp_id, exp_cate)
            return True
        except NotFoundException:
            return False
