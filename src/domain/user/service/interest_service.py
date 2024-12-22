from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Type

from src.config.constant import InterestCategory, Language
from src.domain.mentor.dao.interest_repository import InterestRepository
from src.domain.user.model.common_model import InterestListVO, InterestVO
from src.infra.db.orm.init.user_init import Interest
from src.config.exception import raise_http_exception
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class InterestService:
    def __init__(self, interest_repository: InterestRepository):
        self.__interest_repository: InterestRepository = interest_repository

    async def get_all_interest(self, db: AsyncSession
                               , interest: InterestCategory
                               , language: Language) -> InterestListVO:
        try:
            query: List[Type[Interest]] = await self.__interest_repository.get_all_interest(db, interest,
                                                                                            language.value)

            interests: List[InterestVO] = [self.convert_to_interest_vo(interest) for interest in query]
            return InterestListVO(interests=interests)
        except Exception as e:
            log.error('get_all_interest error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')

    async def get_by_interest_category(self, db: AsyncSession, interest: InterestCategory) -> InterestVO:
        try:
            return self.convert_to_interest_vo(await self.__interest_repository.get_by_interest(db, interest))
        except Exception as e:
            log.error('get_by_interest_category error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')

    async def get_interest_by_ids(self, db: AsyncSession, ids: List[int]) -> InterestListVO:
        try:
            query: List[Type[Interest]] = await self.__interest_repository.get_interest_by_ids(db, ids)

            interests: List[InterestVO] = [self.convert_to_interest_vo(interest) for interest in query]
            return InterestListVO(interests=interests)
        except Exception as e:
            log.error('get_interest_by_ids error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')

    async def get_interest_by_id(self, db: AsyncSession, interest_id: int) -> InterestVO:
        try:
            query: Type[Interest] = await self.__interest_repository.get_interest_by_id(db, interest_id)

            interests: InterestVO = self.convert_to_interest_vo(query)
            return interests
        except Exception as e:
            log.error('get_interest_by_id error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')

    async def get_by_subject_group_and_language(self, db: AsyncSession,
                                                subject_groups: List[str],
                                                language: str = 'CHT') -> Optional[InterestListVO]:
        try:
            interest_list: Optional[List[Type[Interest]]] =\
                await self.__interest_repository.get_by_subject_group_and_language(db, subject_groups, language)
            return self.convert_to_interest_list_vo(interest_list)
        except Exception as e:
            log.error('get_by_subject_group_and_language error: %s', str(e))
            raise_http_exception(e, msg='Internal Server Error')


    def convert_to_interest_vo(self, dto: Optional[Type[Interest]]) -> InterestVO:
        if dto is None:
            return None
        res = InterestVO(**dict(dto.__dict__))
        return res
    def convert_to_interest_list_vo(self, dto: Optional[List[Type[Interest]]]) -> InterestListVO:

        res = InterestListVO(interests=[self.convert_to_interest_vo(dto) for dto in dto] if dto is not None else [])
        return res