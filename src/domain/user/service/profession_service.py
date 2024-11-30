from typing import List, Type, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory
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
        query: List[Optional[Profession]] = await self.__profession_repository.get_profession_by_ids(db, ids)
        professions: List[ProfessionVO] = [Profession.to_profession_vo(q) for q in query]
        return ProfessionListVO(professions=professions)

    async def get_profession_by_id(self, db: AsyncSession
                                   , interest_id: int) -> ProfessionVO:
        query: Optional[Type[Profession]] = await self.__profession_repository.get_profession_by_id(db, interest_id)

        return self.convert_to_profession_vo(query)

    def convert_to_profession_vo(self, dto: Optional[Type[Profession]]) -> Optional[ProfessionVO]:
        if dto is None:
            return None  # return empty object
        profession_id: int = dto.id
        subject: str = dto.subject
        category: ProfessionCategory = ProfessionCategory(dto.category)
        profession_metadata: Dict = dto.profession_metadata
        res: ProfessionVO = ProfessionVO(id=profession_id, subject=subject, category=category,
                                         profession_metadata=profession_metadata, language=dto.language)

        return res
