import asyncio
from typing import Optional, Coroutine, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotAcceptableException, NotFoundException
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.model.common_model import ProfessionVO, InterestListVO, ProfessionListVO
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

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        res: Optional[ProfileDTO] = await self.__profile_repository.upsert_profile(db, dto)
        return await self.convert_to_profile_vo(db, res)

    async def convert_to_profile_vo(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        industry_task: Coroutine[Any, Any, ProfessionVO] = \
            self.__profession_service.get_profession_by_id(db, dto.industry)
        interested_positions_task: Coroutine[Any, Any, InterestListVO] = \
            (self.__interest_service.
             get_by_subject_group_and_language(db, dto.interested_positions, language=dto.language))
        skills_task: Coroutine[Any, Any, InterestListVO] = (self.__interest_service.
                                                            get_by_subject_group_and_language(db,
                                                                                              dto.skills,
                                                                                              language=dto.language))
        topics_task: Coroutine[Any, Any, InterestListVO] = (self.__interest_service.
                                                            get_by_subject_group_and_language(db,
                                                                                              dto.topics,
                                                                                              language=dto.language))
        industry, interested_positions, skills, topics = await asyncio.gather(
            industry_task, interested_positions_task, skills_task, topics_task
        )
        res: ProfileVO = ProfileVO.of(dto)
        res.industry = industry
        res.interested_positions = interested_positions
        res.skills = skills
        res.topics = topics
        return res

    async def convert_to_mentor_profile_vo(self, db: AsyncSession, dto: MentorProfileDTO, language: str) \
            -> MentorProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        industry_task: Coroutine[Any, Any, ProfessionVO] = \
            self.__profession_service.get_profession_by_id(db, dto.industry)
        interested_positions_task: Coroutine[Any, Any, InterestListVO] = \
            (self.__interest_service.
             get_by_subject_group_and_language(db, dto.interested_positions, language=language))
        skills_task: Coroutine[Any, Any, InterestListVO] = (self.__interest_service.
                                                            get_by_subject_group_and_language(db,
                                                                                              dto.skills,
                                                                                              language=language))
        topics_task: Coroutine[Any, Any, InterestListVO] = (self.__interest_service.
                                                            get_by_subject_group_and_language(db,
                                                                                              dto.topics,
                                                                                              language=language))
        expertises_task: Coroutine[Any, Any, ProfessionListVO] = \
            self.__profession_service.get_expertise_by_subjects(db, dto.expertises, language=language)
        industry, interested_positions, skills, topics, expertises = await asyncio.gather(
            industry_task, interested_positions_task, skills_task, topics_task, expertises_task
        )

        res: MentorProfileVO = MentorProfileVO.of(dto)
        res.industry = industry
        res.interested_positions = interested_positions
        res.skills = skills
        res.topics = topics
        res.expertises = expertises
        return res
