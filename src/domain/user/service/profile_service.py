from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotAcceptableException, NotFoundException
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.model.common_model import ProfessionVO, InterestListVO
from src.domain.user.model.user_model import ProfileDTO, ProfileVO
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService


class ProfileService:
    def __init__(self,
                 interest_service: InterestService,
                 profile_repository: ProfileRepository,
                 profession_service: ProfessionService):
        self.__interest_service: InterestService = interest_service
        self.__profession_service: ProfessionService = profession_service
        self.__profile_repository: ProfileRepository = profile_repository

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileVO:
        if user_id is None:
            raise NotAcceptableException(msg="No user interest_id is provided")

        return await self.convert_to_profile_vo(db, await self.__profile_repository.get_by_user_id(db, user_id))

    async def get_by_conditions(self, db: AsyncSession, dto: ProfileDTO) -> List[ProfileDTO]:
        return await self.__profile_repository.get_profiles_by_conditions(db, dto)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        res: Optional[ProfileDTO] = await self.__profile_repository.upsert_profile(db, dto)
        return await self.convert_to_profile_vo(db, res)

    async def convert_to_profile_vo(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        industry: Optional[ProfessionVO] = await self.__profession_service.get_profession_by_id(db, dto.industry)
        interested_positions: Optional[InterestListVO] = \
            await self.__interest_service.get_interest_by_ids(db, dto.interested_positions)
        skills: Optional[InterestListVO] = await self.__interest_service.get_interest_by_ids(db, dto.skills)
        topics: Optional[InterestListVO] = await self.__interest_service.get_interest_by_ids(db, dto.topics)
        res: ProfileVO = ProfileVO.of(dto)
        res.industry = industry
        res.interested_positions = interested_positions
        res.skills = skills
        res.topics = topics
        return res

    async def convert_to_mentor_profile_vo(self, db: AsyncSession, dto: MentorProfileDTO):
        if dto is None:
            raise NotFoundException(msg="no data found")
        industry: Optional[ProfessionVO] = await self.__profession_service.get_profession_by_id(db, dto.industry)
        interested_positions: Optional[InterestListVO] = \
            await self.__interest_service.get_interest_by_ids(db, dto.interested_positions)
        skills: Optional[InterestListVO] = await self.__interest_service.get_interest_by_ids(db, dto.skills)
        topics: Optional[InterestListVO] = await self.__interest_service.get_interest_by_ids(db, dto.topics)
        res: MentorProfileVO = MentorProfileVO.of(dto)
        res.industry = industry
        res.interested_positions = interested_positions
        res.skills = skills
        res.topics = topics
        return res
