from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ExperienceCategory
from src.config.exception import NotFoundException, ServerException
from src.domain.mentor.model.experience_model import ExperienceVO, ExperienceDTO, ExperienceListVO
from src.domain.user.model.common_model import InterestVO
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
            return [ExperienceVO.model_validate(exp) for exp in mentor_exp]
        except Exception as e:
            log.error(f'get_exp_list_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience list response failed')

    # FIXME: 育志，為什麼透過u ser_id 去取得的經驗只會有一種？應該包含 學歷/經歷/LINK ... 多種經驗
    # 我用 get_exp_list_by_user_id 實現的函數你可以參考一下
    async def get_exp_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[ExperienceVO]:
        try:
            mentor_exp_list: List[MentorExperience] = \
                await self.__exp_dao.get_mentor_exp_list_by_user_id(db, user_id)
            if not mentor_exp_list:
                return []
            
            experiences = [ExperienceVO.model_validate(exp) for exp in mentor_exp_list]
            return ExperienceListVO(experiences=experiences)
        except Exception as e:
            log.error(f'get_exp_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience response failed')

    async def upsert_exp(self, db: AsyncSession, 
                         user_id: int,
                         experience_dto: ExperienceDTO) -> ExperienceVO:
        try:
            mentor_exp: MentorExperience = await self.__exp_dao.upsert_mentor_exp_by_user_id(db=db,
                                                                                            user_id=user_id,
                                                                                            mentor_exp_dto=experience_dto)
            res: ExperienceVO = ExperienceVO.model_validate(mentor_exp)

            return res
        except Exception as e:
            log.error(f'upsert_exp error: %s', str(e))
            raise ServerException(msg='upsert experience response failed')

    async def delete_exp_by_user_and_exp_id(self, db: AsyncSession, 
                                            user_id: int, 
                                            experience_dto: ExperienceDTO) -> bool:
        try:
            res: bool = await self.__exp_dao.delete_mentor_exp_by_id(db, user_id, experience_dto)
            if not res:
                exp_id = experience_dto.id
                log.info('user_id: %s No such experience with id: %s', user_id, exp_id)
            return res
        except Exception as e:
            log.error(f'delete_exp_by_user_and_exp_id error: %s', str(e))
            raise ServerException(msg=f'delete experience response failed: user_id: {user_id}, exp_id: {exp_id}')


    # 是否為 Onboarding, 透過是否有填寫完個人資料判斷
    @staticmethod
    def is_onboarding(all_interests: Optional[Dict[str, List[InterestVO]]]) -> bool:
        if all_interests is None:
            return False
        
        for interest_category, interests in all_interests.items():
            if len(interests) == 0:
                log.info(f'{interest_category} is not filled')
                return False
        
        return True

    # 是否為 Mentor, 透過是否有填寫足夠的經驗類別判斷
    @staticmethod
    def is_mentor(experiences: List[ExperienceVO]) -> bool:
        exp_categories = set()
        for exp in experiences:
            if exp.category:
                exp_categories.add(exp.category)

        # 如果有填寫至少 2 種經驗類別, 則視為已完成 Mentor
        return (len(exp_categories) >= 2)
