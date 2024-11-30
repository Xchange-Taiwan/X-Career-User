import asyncio

from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.model.common_model import ProfessionVO, InterestListVO, ProfessionListVO
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService


class MentorService:
    def __init__(self, mentor_repository: MentorRepository, profile_repository: ProfileRepository,
                 interest_service: InterestService, profession_service: ProfessionService):
        self.__mentor_repository: MentorRepository = mentor_repository
        self.__interest_service: InterestService = interest_service
        self.__profession_service: ProfessionService = profession_service
        self.__profile_repository: ProfileRepository = profile_repository

    async def upsert_mentor_profile(self, db: AsyncSession, profile_dto: MentorProfileDTO) -> MentorProfileVO:
        res_dto: MentorProfileDTO = await self.__mentor_repository.upsert_mentor(db, profile_dto)
        res_vo: MentorProfileVO = await self.convert_to_mentor_profile_vo(db, res_dto)
        return res_vo

    async def get_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        mentor_dto: MentorProfileDTO = await self.__mentor_repository.get_mentor_profile_by_id_and_language(db, user_id,
                                                                                                            language)
        if (mentor_dto is None):
            raise NotFoundException(msg=f"No such user with id: {user_id}, language: {language}")
        return await self.convert_to_mentor_profile_vo(db, mentor_dto)

    async def convert_to_mentor_profile_vo(self, db: AsyncSession, dto: MentorProfileDTO) -> MentorProfileVO:

        res: MentorProfileVO = MentorProfileVO.of(dto)
        res.expertises = await self.__profession_service.get_profession_by_ids(db, dto.expertises)
        return res
