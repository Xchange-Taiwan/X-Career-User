from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import DEFAULT_LANGUAGE
from src.config.exception import NotFoundException, ServerException, raise_http_exception
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService
from src.domain.user.service.profile_service import ProfileService
from src.domain.user.service.tag_service import TagService
import logging

log = logging.getLogger(__name__)

class MentorService:
    def __init__(self, mentor_repository: MentorRepository, profile_repository: ProfileRepository,
                 interest_service: InterestService, profession_service: ProfessionService,
                 profile_service: ProfileService, tag_service: TagService):
        self.__mentor_repository: MentorRepository = mentor_repository
        self.__interest_service: InterestService = interest_service
        self.__profession_service: ProfessionService = profession_service
        self.__profile_repository: ProfileRepository = profile_repository
        self.__profile_service: ProfileService = profile_service
        self.__tag_service: TagService = tag_service

    async def upsert_mentor_profile(self, db: AsyncSession, profile_dto: MentorProfileDTO) -> MentorProfileVO:
        try:
            language = profile_dto.language or DEFAULT_LANGUAGE

            # Read existing arrays first so untouched buckets survive the
            # per-bucket replace semantics (None = leave alone, [] = clear).
            # First-time mentors won't have a row yet — fall back to empty.
            existing = await self.__mentor_repository.find_profile_by_user_id(
                db, profile_dto.user_id,
            )
            existing_want = list(existing.want_tags or []) if existing else []
            existing_have = list(existing.have_tags or []) if existing else []

            new_want, new_have = await self.__tag_service.merge_buckets_to_arrays(
                db,
                current_want_tags=existing_want,
                current_have_tags=existing_have,
                language=language,
                want_position=profile_dto.want_position,
                want_skill=profile_dto.want_skill,
                want_topic=profile_dto.want_topic,
                have_skill=profile_dto.have_skill,
                have_topic=profile_dto.have_topic,
            )
            # Stamp the merged arrays back onto the dto so the upsert's
            # convert_dto_to_model picks them up — Profile.want_tags/have_tags
            # are 1:1 columns, the 5 input buckets aren't.
            profile_dto.want_tags = new_want
            profile_dto.have_tags = new_have

            res_dto: MentorProfileDTO = await self.__mentor_repository.upsert_mentor(db, profile_dto)

            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(
                db, res_dto, language=language,
            )
            await self.__hydrate_buckets(db, res_vo, res_dto, language)
            return res_vo
        except Exception as e:
            log.error(f'upsert_mentor_profile error: %s', str(e))
            err_msg = getattr(e, 'msg', 'upsert mentor profile response failed')
            raise ServerException(msg=err_msg)

    async def get_mentor_profile_by_id(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        try:
            mentor_dto: MentorProfileDTO = await self.__mentor_repository.get_mentor_profile_by_id(db, user_id)
            if mentor_dto is None:
                raise NotFoundException(msg=f"No such user with id: {user_id}")
            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(
                db, mentor_dto, language=language,
            )
            await self.__hydrate_buckets(db, res_vo, mentor_dto, language)
            return res_vo
        except Exception as e:
            log.error(f'get_mentor_profile_by_id error: %s', str(e))
            err_msg = getattr(e, 'msg', 'get mentor profile response failed')
            raise_http_exception(e, msg=err_msg)

    async def __hydrate_buckets(
        self,
        db: AsyncSession,
        vo: MentorProfileVO,
        dto: MentorProfileDTO,
        language: str,
    ) -> None:
        # Best-effort: hydration failure shouldn't fail the whole profile read.
        # Empty buckets ([]) are explicit on the wire so the frontend can
        # distinguish "user has none" from "field absent".
        try:
            buckets = await self.__tag_service.hydrate_buckets(
                db,
                want_tags=list(dto.want_tags or []),
                have_tags=list(dto.have_tags or []),
                language=language,
            )
        except Exception as e:
            log.warning("hydrate buckets failed for user %s: %s", dto.user_id, e)
            buckets = {
                'want_position': [], 'want_skill': [], 'want_topic': [],
                'have_skill': [], 'have_topic': [],
            }
        vo.want_position = buckets['want_position']
        vo.want_skill = buckets['want_skill']
        vo.want_topic = buckets['want_topic']
        vo.have_skill = buckets['have_skill']
        vo.have_topic = buckets['have_topic']
