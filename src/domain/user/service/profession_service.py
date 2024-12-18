import logging as log
from typing import List, Type, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory, Language
from src.config.exception import raise_http_exception
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.user.model.common_model import ProfessionListVO, ProfessionVO
from src.infra.db.orm.init.user_init import Profession

log.basicConfig(filemode='w', level=log.INFO)


class ProfessionService:
    def __init__(self, profession_repository: ProfessionRepository):
        self.__profession_repository: ProfessionRepository = profession_repository

    async def get_all_profession_by_category_and_language(self, db: AsyncSession
                                                          , profession: ProfessionCategory
                                                          , language: Language) -> ProfessionListVO:
        try:
            res: ProfessionListVO = ProfessionListVO()
            professions: List[Type[Profession]] = \
                await self.__profession_repository.get_all_profession(db, profession, language.value)
            res.professions = [self.convert_to_profession_vo(profession) for profession in professions]
            return res
        except Exception as e:
            log.error('get_all_profession_by_category_and_language error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')



    async def get_industries_by_subjects(self, db: AsyncSession,
                                         subject_groups: List[str],
                                         language: str) -> ProfessionListVO:
        try:
            res: List[Type[Profession]] = \
                await self.__profession_repository.get_profession_by_subjects_and_category(db,
                                                                                           subject_groups,
                                                                                           ProfessionCategory.INDUSTRY,
                                                                                           language)
            professions: List[ProfessionVO] = [self.convert_to_profession_vo(p) for p in res]
            profession_list_vo: ProfessionListVO = ProfessionListVO(professions=professions)
            return profession_list_vo
        except Exception as e:
            log.error('get_industries_by_subjects error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')

    async def get_expertise_by_subjects(self, db: AsyncSession,
                                        subject_groups: List[str],
                                        language: str) -> ProfessionListVO:
        try:
            res: List[Type[Profession]] = \
                await self.__profession_repository.get_profession_by_subjects_and_category(db,
                                                                                           subject_groups,
                                                                                           ProfessionCategory.EXPERTISE,
                                                                                           language)
            professions: List[ProfessionVO] = [self.convert_to_profession_vo(p) for p in res]
            profession_list_vo: ProfessionListVO = ProfessionListVO(professions=professions)
            return profession_list_vo
        except Exception as e:
            log.error('get_expertise_by_subjects error: %s', str(e))
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
