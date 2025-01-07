import asyncio
import logging as log
from typing import Optional, Coroutine, Any, Set, Dict, List, Union

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import InterestCategory, ExperienceCategory
from src.config.exception import (
    NotAcceptableException,
    NotFoundException,
    ServerException,
    raise_http_exception,
)
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.mentor.model.experience_model import ExperienceVO
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.model.common_model import (
    ProfessionVO,
    InterestVO,
    InterestListVO,
    ProfessionListVO,
)
from src.domain.user.model.user_model import ProfileDTO, ProfileVO
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService

log.basicConfig(filemode="w", level=log.INFO)


class ProfileService:
    def __init__(
        self,
        interest_service: InterestService,
        profession_service: ProfessionService,
        experience_service: ExperienceService,
        profile_repository: ProfileRepository,
    ):
        self.__interest_service: InterestService = interest_service
        self.__profession_service: ProfessionService = profession_service
        self.__exp_service: ExperienceService = experience_service
        self.__profile_repository: ProfileRepository = profile_repository

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int, language: Optional[str] = None
    ) -> ProfileVO:
        try:
            if user_id is None:
                raise NotAcceptableException(msg="No user interest_id is provided")

            dto: ProfileDTO = await self.__profile_repository.get_by_user_id(
                db, user_id
            )
            return await self.convert_to_profile_vo(db, dto, language=language)
        except Exception as e:
            log.error(f"get_by_user_id error: %s", str(e))
            err_msg = getattr(e, "msg", "get profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        try:
            res: Optional[ProfileDTO] = await self.__profile_repository.upsert_profile(
                db, dto
            )
            return await self.convert_to_profile_vo(db, res)
        except Exception as e:
            log.error(f"upsert_profile error: %s", str(e))
            err_msg = getattr(e, "msg", "upsert profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def convert_to_profile_vo(
        self, db: AsyncSession, dto: ProfileDTO, language: Optional[str] = None
    ) -> ProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        if language is None:
            language = dto.language

        try:
            user_id = dto.user_id
            experiences: List[ExperienceVO] = (
                await self.__exp_service.get_exp_list_by_user_id(db, user_id)
            )
            industries: ProfessionListVO = (
                await self.__profession_service.get_industries_by_subjects(
                    db, [dto.industry], language
                )
            )

            # get all interests: interest_positions, skills, topics
            all_interests: Optional[Dict[str, List[InterestVO]]] = (
                await self.get_all_interests(db, dto, language)
            )

            res: ProfileVO = ProfileVO.of(dto)
            if len(industries.professions) > 0:
                res.industry = industries.professions[0]
            if all_interests:
                res.interested_positions = InterestListVO(
                    interests=all_interests[InterestCategory.INTERESTED_POSITION.value]
                )
                res.skills = InterestListVO(
                    interests=all_interests[InterestCategory.SKILL.value]
                )
                res.topics = InterestListVO(
                    interests=all_interests[InterestCategory.TOPIC.value]
                )

            # 是否為 Onboarding, 透過是否有填寫完個人資料判斷
            res.onboarding = ExperienceService.is_onboarding(dto, all_interests)
            # 是否為 Mentor, 透過是否有填寫足夠的經驗類別判斷
            res.is_mentor = ExperienceService.is_mentor(experiences)
            res.language = language
            return res

        except Exception as e:
            log.error(f"convert_to_profile_vo error: %s", str(e))
            err_msg = getattr(e, "msg", "profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def convert_to_mentor_profile_vo(
        self, db: AsyncSession, dto: MentorProfileDTO, language: Optional[str] = None
    ) -> MentorProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        if language is None:
            language = dto.language

        try:
            user_id = dto.user_id
            experiences: List[ExperienceVO] = (
                await self.__exp_service.get_exp_list_by_user_id(db, user_id)
            )
            industries: ProfessionListVO = (
                await self.__profession_service.get_industries_by_subjects(
                    db, [dto.industry], language=language
                )
            )
            expertises: ProfessionListVO = (
                await self.__profession_service.get_expertise_by_subjects(
                    db, dto.expertises, language=language
                )
            )

            # get all interests: interest_positions, skills, topics
            all_interests: Optional[Dict[str, List[InterestVO]]] = (
                await self.get_all_interests(db, dto, language)
            )

            res: MentorProfileVO = MentorProfileVO.of(dto)
            res.expertises = expertises

            if len(industries.professions) > 0:
                res.industry = industries.professions[0]
            if all_interests:
                res.interested_positions = InterestListVO(
                    interests=all_interests[InterestCategory.INTERESTED_POSITION.value]
                )
                res.skills = InterestListVO(
                    interests=all_interests[InterestCategory.SKILL.value]
                )
                res.topics = InterestListVO(
                    interests=all_interests[InterestCategory.TOPIC.value]
                )

            # mentor experiences
            res.experiences = experiences
            # 是否為 Onboarding, 透過是否有填寫完個人資料判斷
            res.onboarding = ExperienceService.is_onboarding(dto, all_interests)
            # 是否為 Mentor, 透過是否有填寫足夠的經驗類別判斷
            res.is_mentor = ExperienceService.is_mentor(experiences)
            res.language = language
            return res

        except Exception as e:
            log.error(f"convert_to_mentor_profile_vo error: %s", str(e))
            err_msg = getattr(e, "msg", "mentor profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def get_all_interests(
        self, db: AsyncSession, dto: ProfileDTO, language: str
    ) -> Optional[Dict[str, List[InterestVO]]]:
        all_subject_groups: List = dto.get_all_subject_groups()
        # don't need to query DB if there is no subject group
        if not all_subject_groups:
            return None

        all_interests: InterestListVO = (
            await self.__interest_service.get_by_subject_group_and_language(
                db, all_subject_groups, language=language
            )
        )
        # don't need to convert if there is no interest
        if not all_interests.interests:
            return None

        return dto.get_all_interest_details(all_interests)
