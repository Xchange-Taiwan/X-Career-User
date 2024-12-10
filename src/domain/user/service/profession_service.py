from typing import List, Type, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory, Language
from src.config.exception import raise_http_exception
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.user.model.common_model import ProfessionListVO, ProfessionVO
from src.infra.db.orm.init.user_init import Profession
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ProfessionService:
    def __init__(self, profession_repository: ProfessionRepository):
        self.__profession_repository: ProfessionRepository = profession_repository

    async def get_all_profession(self, db: AsyncSession
                                 , profession: ProfessionCategory
                                 , language: Language) -> ProfessionListVO:
        try:
            res: ProfessionListVO = ProfessionListVO(language=language.value)
            interests: List[Type[Profession]] = \
                await self.__profession_repository.get_all_profession(db, profession, language.value)
            res.professions = [self.convert_to_profession_vo(interest) for interest in interests]
            return res
        except Exception as e:
            log.error('get_all_profession error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')


    async def get_by_profession_category(self, db: AsyncSession
                                         , profession: ProfessionCategory) -> ProfessionVO:
        try:
            return self.convert_to_profession_vo(
                await self.__profession_repository.get_by_profession_category(db, profession))
        except Exception as e:
            log.error('get_by_profession_category error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')


    async def get_profession_by_ids(self, db: AsyncSession
                                    , ids: List[int]) -> ProfessionListVO:
        try:
            query: List[Type[Profession]] = await self.__profession_repository.get_profession_by_ids(db, ids)
            res = [self.convert_to_profession_vo(profession) for profession in query]
            return ProfessionListVO(profession=res)
        except Exception as e:
            log.error('get_profession_by_ids error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')


    async def get_profession_by_id(self, db: AsyncSession
                                   , interest_id: int) -> ProfessionVO:
        try:
            query: Optional[Type[Profession]] = await self.__profession_repository.get_profession_by_id(db, interest_id)
            return self.convert_to_profession_vo(query)
        except Exception as e:
            log.error('get_profession_by_id error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')


    def convert_to_profession_vo(self, dto: Optional[Type[Profession]]) -> Optional[ProfessionVO]:
        if dto is None:
            return None  # return empty object
        profession_id: int = dto.id
        category: ProfessionCategory = ProfessionCategory(dto.category)
        subject_group: str = dto.subject_group
        subject: str = dto.subject
        profession_metadata: Dict = dto.profession_metadata
        res: ProfessionVO = ProfessionVO(
            id=profession_id, 
            category=category,
            subject_group=subject_group,
            subject=subject, 
            profession_metadata=profession_metadata, 
            language=dto.language)

        return res
