from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing_extensions import Type

from src.config.constant import InterestCategory
from src.config.exception import NotFoundException
from src.domain.mentor.dao.interest_repository import InterestRepository
from src.domain.user.model.common_model import InterestListVO, InterestVO
from src.infra.db.orm.init.user_init import Interest


class InterestService:
    def __init__(self, interest_repository: InterestRepository):
        self.__interest_repository: InterestRepository = interest_repository

    async def get_all_interest(self, db: AsyncSession) -> InterestListVO:
        query: List[Type[Interest]] = await self.__interest_repository.get_all_interest(db)

        interests: List[InterestVO] = [self.convert_to_interest_VO(interest) for interest in query]
        return InterestListVO(interests=interests)

    async def get_by_interest_category(self, db: AsyncSession, interest: InterestCategory) -> InterestVO:
        return self.convert_to_interest_VO(await self.__interest_repository.get_by_interest(db, interest))

    async def get_interest_by_ids(self, db: AsyncSession, ids: List[int]) -> InterestListVO:
        query: List[Type[Interest]] = await self.__interest_repository.get_interest_by_ids(db, ids)

        interests: List[InterestVO] = [self.convert_to_interest_VO(interest) for interest in query]
        return InterestListVO(interests=interests)

    async def get_interest_by_id(self, db: AsyncSession, interest_id: int) -> InterestVO:
        query: Type[Interest] = await self.__interest_repository.get_interest_by_id(db, interest_id)

        interests: InterestVO = self.convert_to_interest_VO(query)
        return interests
    def convert_to_interest_VO(self, dto: Optional[Type[Interest]]) -> InterestVO:
        if not dto:
            raise NotFoundException(msg="no data found")
        res = InterestVO(**dict(dto.__dict__))
        return res
