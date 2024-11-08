import asyncio

from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
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
        await db.commit()
        return res_vo

    async def get_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        mentor_dto: MentorProfileDTO = await self.__mentor_repository.get_mentor_profile_by_id_and_language(db, user_id,
                                                                                                            language)

        return await self.convert_to_mentor_profile_vo(db, mentor_dto)

    async def convert_to_mentor_profile_vo(self, db: AsyncSession, dto: MentorProfileDTO) -> MentorProfileVO:
        try:
            # coroutines neeed to be awaited
            industry_task = asyncio.create_task(self.__profession_service.get_profession_by_id(db, dto.industry))
            interested_positions_task = asyncio.create_task(
                self.__interest_service.get_interest_by_ids(db, dto.interested_positions))
            skills_task = asyncio.create_task(self.__interest_service.get_interest_by_ids(db, dto.skills))
            topics_task = asyncio.create_task(self.__interest_service.get_interest_by_ids(db, dto.topics))
            expertises_task = asyncio.create_task(self.__profession_service.get_profession_by_ids(db, dto.expertises))

            # Await all tasks concurrently
            industry, interested_positions, skills, topics, expertises = await asyncio.gather(
                industry_task, interested_positions_task, skills_task, topics_task, expertises_task
            )
            user_id = dto.user_id
            name = dto.name
            avatar = dto.avatar
            timezone = dto.timezone
        except ArgumentError:
            raise NotFoundException(msg="無該會員資料, 可能是會員id有誤")
        position = dto.position
        company = dto.company
        linkedin_profile = dto.linkedin_profile

        location = dto.location
        personal_statement = dto.personal_statement
        about = dto.about
        seniority_level = dto.seniority_level
        experience = dto.experience
        language = dto.language

        return MentorProfileVO(
            user_id=user_id,
            name=name,
            avatar=avatar,
            topics=topics,
            timezone=timezone,
            industry=industry,
            position=position,
            company=company,
            linkedin_profile=linkedin_profile,
            interested_positions=interested_positions,
            skills=skills,
            #location=location,
            personal_statement=personal_statement,
            about=about,
            seniority_level=seniority_level,
            expertises=expertises,
            #experience=experience,
            language=language
        )
