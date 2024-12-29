from typing import Dict, List, Optional

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

    async def get_exp_list_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[List[ExperienceVO]]:
        try:
            mentor_exp: List[MentorExperience] = await self.__exp_dao.get_mentor_exp_list_by_user_id(db, user_id)
            if not mentor_exp:
                return []
            return [ExperienceVO.from_orm(exp) for exp in mentor_exp]
        except Exception as e:
            log.error(f'get_exp_list_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience list response failed')

    # FIXME: 育志，為什麼透過u ser_id 去取得的經驗只會有一種？應該包含 學歷/經歷/LINK ... 多種經驗
    # 我用 get_exp_list_by_user_id 實現的函數你可以參考一下
    async def get_exp_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[ExperienceVO]:
        try:
            mentor_exp: MentorExperience = await self.__exp_dao.get_mentor_exp_by_user_id(db, user_id)
            if not mentor_exp:
                return None
            return ExperienceVO.from_orm(mentor_exp)
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
            res: ExperienceVO = ExperienceVO.from_orm(mentor_exp)

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
