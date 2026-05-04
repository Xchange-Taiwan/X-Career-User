import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constant import ProfessionCategory, TagKind
from src.config.exception import (
    NotAcceptableException,
    NotFoundException,
    raise_http_exception,
)
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.mentor.model.experience_model import ExperienceVO
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.model.common_model import ProfessionVO
from src.domain.user.model.user_model import ProfileDTO, ProfileVO
from src.domain.user.service.tag_service import TagService

log = logging.getLogger(__name__)

class ProfileService:
    def __init__(
        self,
        tag_service: TagService,
        experience_service: ExperienceService,
        profile_repository: ProfileRepository,
    ):
        self.__tag_service: TagService = tag_service
        self.__exp_service: ExperienceService = experience_service
        self.__profile_repository: ProfileRepository = profile_repository

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int, language: Optional[str] = None
    ) -> ProfileVO:
        try:
            if user_id is None:
                raise NotAcceptableException(msg="No user_id is provided")

            dto, want_tags, _ = await self.__profile_repository.get_by_user_id(
                db, user_id
            )
            return await self.convert_to_profile_vo(
                db, dto, language=language, want_tags=want_tags,
            )
        except Exception as e:
            log.error(f"get_by_user_id error: %s", str(e))
            err_msg = getattr(e, "msg", "get profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileVO:
        try:
            res, want_tags, _ = await self.__profile_repository.upsert_profile(
                db, dto
            )
            return await self.convert_to_profile_vo(db, res, want_tags=want_tags)
        except Exception as e:
            log.error(f"upsert_profile error: %s", str(e))
            err_msg = getattr(e, "msg", "upsert profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def convert_to_profile_vo(
        self,
        db: AsyncSession,
        dto: ProfileDTO,
        language: Optional[str] = None,
        *,
        want_tags: Optional[List[str]] = None,
    ) -> ProfileVO:
        if dto is None:
            raise NotFoundException(msg="no data found")
        if language is None:
            language = dto.language

        try:
            res: ProfileVO = ProfileVO.of(dto)
            res.industry = await self.__resolve_industry(db, dto.industry, language)
            res.onboarding = ExperienceService.is_onboarded(want_tags)
            res.is_mentor = dto.is_mentor
            res.language = language
            return res

        except Exception as e:
            log.error(f"convert_to_profile_vo error: %s", str(e))
            err_msg = getattr(e, "msg", "profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def convert_to_mentor_profile_vo(
        self,
        db: AsyncSession,
        dto: MentorProfileDTO,
        language: Optional[str] = None,
        *,
        want_tags: Optional[List[str]] = None,
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

            res: MentorProfileVO = MentorProfileVO.of(dto)
            res.industry = await self.__resolve_industry(db, dto.industry, language)
            res.experiences = experiences
            res.onboarding = ExperienceService.is_onboarded(want_tags)
            res.is_mentor = dto.is_mentor
            res.language = language
            return res

        except Exception as e:
            log.error(f"convert_to_mentor_profile_vo error: %s", str(e))
            err_msg = getattr(e, "msg", "mentor profile response failed")
            raise_http_exception(e, msg=err_msg)

    async def __resolve_industry(
        self,
        db: AsyncSession,
        subject_group: Optional[str],
        language: str,
    ) -> Optional[ProfessionVO]:
        # Industry catalog now lives in `tags` (kind='industry'); the
        # ProfessionVO shape is preserved on the wire so the frontend
        # cutover in Tracker #249 can happen without an API contract change.
        # Returns None when industry isn't set or the subject_group doesn't
        # resolve — same behavior as the legacy professions lookup.
        tag = await self.__tag_service.hydrate_flat_tag(
            db, TagKind.INDUSTRY, subject_group, language,
        )
        if tag is None:
            return None
        return ProfessionVO.from_tag(tag, ProfessionCategory.INDUSTRY)
