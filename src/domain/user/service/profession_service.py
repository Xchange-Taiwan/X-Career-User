import logging as log
from typing import List, Type, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import CACHE_TTL
from src.config.constant import ProfessionCategory, Language
from src.config.exception import raise_http_exception
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.user.model.common_model import ProfessionListVO, ProfessionVO
from src.infra.db.orm.init.user_init import Profession
from src.infra.cache.local_cache import LocalCache

log.basicConfig(filemode="w", level=log.INFO)


class ProfessionService:
    def __init__(self, profession_repository: ProfessionRepository, cache: LocalCache):
        self.__profession_repository: ProfessionRepository = profession_repository
        # 常數資料可用 local cache
        self.cache = cache

    async def get_all_profession_by_category_and_language(
        self, db: AsyncSession, profession: ProfessionCategory, language: Language
    ) -> ProfessionListVO:
        try:
            cache_key = self.cache_key(profession, language.value)
            cache_res: ProfessionListVO = await self.cache.get(cache_key)
            if cache_res:
                return cache_res

            all_list_vo: ProfessionListVO = ProfessionListVO()
            professions: List[Type[Profession]] = (
                await self.__profession_repository.get_all_profession(
                    db, profession, language.value
                )
            )
            all_list_vo.professions = [
                self.convert_to_profession_vo(profession) for profession in professions
            ]
            # set local cache
            await self.cache.set(cache_key, all_list_vo, CACHE_TTL)
            return all_list_vo
        except Exception as e:
            log.error("get_all_profession_by_category_and_language error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def get_industries_by_subjects(
        self, db: AsyncSession, subject_groups: List[str], language: str
    ) -> ProfessionListVO:
        try:
            cache_key = self.cache_key(ProfessionCategory.INDUSTRY, language)
            cache_res: ProfessionListVO = await self.cache.get(cache_key)
            if cache_res:
                return self.filter_by_subject_group(cache_res, subject_groups)

            res: List[Type[Profession]] = (
                await self.__profession_repository.get_all_profession(
                    db, ProfessionCategory.INDUSTRY, language
                )
            )
            professions: List[ProfessionVO] = [
                self.convert_to_profession_vo(p) for p in res
            ]
            all_list_vo: ProfessionListVO = ProfessionListVO(professions=professions)
            # set local cache
            await self.cache.set(cache_key, all_list_vo, CACHE_TTL)
            sub_list_vo = self.filter_by_subject_group(all_list_vo, subject_groups)
            return sub_list_vo
        except Exception as e:
            log.error("get_industries_by_subjects error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    async def get_expertise_by_subjects(
        self, db: AsyncSession, subject_groups: List[str], language: str
    ) -> ProfessionListVO:
        try:
            cache_key = self.cache_key(ProfessionCategory.EXPERTISE, language)
            cache_res: ProfessionListVO = await self.cache.get(cache_key)
            if cache_res:
                return self.filter_by_subject_group(cache_res, subject_groups)

            res: List[Type[Profession]] = (
                await self.__profession_repository.get_all_profession(
                    db, ProfessionCategory.EXPERTISE, language
                )
            )
            professions: List[ProfessionVO] = [
                self.convert_to_profession_vo(p) for p in res
            ]
            all_list_vo: ProfessionListVO = ProfessionListVO(professions=professions)
            # set local cache
            await self.cache.set(cache_key, all_list_vo, CACHE_TTL)
            sub_list_vo = self.filter_by_subject_group(all_list_vo, subject_groups)
            return sub_list_vo
        except Exception as e:
            log.error("get_expertise_by_subjects error: %s", str(e))
            raise_http_exception(e, msg="Internal Server Error")

    def convert_to_profession_vo(
        self, dto: Optional[Type[Profession]]
    ) -> Optional[ProfessionVO]:
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
            language=dto.language,
        )

        return res

    def cache_key(self, profession: ProfessionCategory, language: str):
        return f"profession_{profession.value}_{language}"

    def filter_by_subject_group(
        self, list_vo: ProfessionListVO, subject_groups: List[str]
    ) -> ProfessionListVO:
        sub_list_vo = ProfessionListVO(professions=[])
        sub_list_vo.professions = [
            p for p in list_vo.professions if p.subject_group in subject_groups
        ]
        return sub_list_vo
