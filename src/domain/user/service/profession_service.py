from typing import List, Type, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory
from src.config.exception import NotFoundException
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.user.model.common_model import ProfessionListVO, ProfessionVO
from src.infra.db.orm.init.user_init import Profession


class ProfessionService:
    def __init__(self, profession_repository: ProfessionRepository):
        self.__profession_repository: ProfessionRepository = profession_repository

    async def get_all_profession(self, db: AsyncSession) -> ProfessionListVO:
        res: ProfessionListVO = ProfessionListVO()
        interests: List[Type[Profession]] = await self.__profession_repository.get_all_profession(db)
        res.professions = [self.convert_to_profession_vo(interest) for interest in interests]
        return res

    async def get_by_profession_category(self, db: AsyncSession
                                         , profession: ProfessionCategory) -> ProfessionVO:
        return self.convert_to_profession_vo(
            await self.__profession_repository.get_by_profession_category(db, profession))

    async def get_profession_by_ids(self, db: AsyncSession
                                    , ids: List[int]) -> ProfessionListVO:
        query: List[Type[Profession]] = await self.__profession_repository.get_profession_by_ids(db, ids)
        res = [self.convert_to_profession_vo(profession) for profession in query]
        return ProfessionListVO(profession=res)

    async def get_profession_by_id(self, db: AsyncSession
                                   , interest_id: int) -> ProfessionVO:
        query: Optional[Type[Profession]] = await self.__profession_repository.get_profession_by_id(db, interest_id)

        return self.convert_to_profession_vo(query)

    def convert_to_profession_vo(self, dto: Optional[Type[Profession]]) -> ProfessionVO:
        if dto is None:
            raise NotFoundException(msg="no profession data found")
        id: int = dto.id
        subject: str = dto.subject
        category: ProfessionCategory = ProfessionCategory(dto.category)
        profession_metadata: Dict = dto.profession_metadata
        res: ProfessionVO = ProfessionVO(id=id, subject=subject, category=category,
                                         profession_metadata=profession_metadata)

        return res
