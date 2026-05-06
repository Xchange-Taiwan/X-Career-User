from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import DEFAULT_LANGUAGE
from src.config.exception import NotFoundException, raise_http_exception
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.model.experience_model import ExperienceVO
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.service.profile_service import ProfileService
from src.domain.user.service.tag_service import TagService
import logging

log = logging.getLogger(__name__)

class MentorService:
    def __init__(self, mentor_repository: MentorRepository, profile_repository: ProfileRepository,
                 profile_service: ProfileService, tag_service: TagService):
        self.__mentor_repository: MentorRepository = mentor_repository
        self.__profile_repository: ProfileRepository = profile_repository
        self.__profile_service: ProfileService = profile_service
        self.__tag_service: TagService = tag_service

    async def upsert_mentor_profile(self, db: AsyncSession, profile_dto: MentorProfileDTO) -> MentorProfileVO:
        try:
            language = profile_dto.language or DEFAULT_LANGUAGE

            # Pull the existing row so untouched buckets / experiences survive
            # the three-state replace semantics (None = leave alone, [] = clear,
            # [...] = replace). First-time mentors won't have a row yet.
            existing = await self.__mentor_repository.find_profile_by_user_id(
                db, profile_dto.user_id,
            )
            if existing is None:
                existing_want, existing_have = [], []
                existing_experiences: List[dict] = []
            else:
                existing_dto, existing_want, existing_have = existing
                # mode='json' so the ExperienceCategory enum becomes its
                # string value — asyncpg's JSONB encoder can't handle Enum.
                existing_experiences = [
                    e.model_dump(mode='json') for e in (existing_dto.experiences or [])
                ]

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

            # Resolve experiences three-state into the actual list to persist.
            # None means "don't touch the column"; we still need the resolved
            # list to recompute is_mentor below, so fall back to existing.
            if profile_dto.experiences is None:
                resolved_experiences = existing_experiences
                column_payload: Optional[List[dict]] = None
            else:
                # mode='json' for the same JSONB-encoder reason as above.
                resolved_experiences = [
                    e.model_dump(mode='json') for e in profile_dto.experiences
                ]
                column_payload = resolved_experiences

            # is_mentor is derived from experiences, so recompute it here
            # rather than trusting whatever the dto carries — this is the only
            # write path that can flip the flag.
            resolved_vo_list = [
                ExperienceVO.model_validate(e) for e in resolved_experiences
            ]
            new_is_mentor = ExperienceService.is_mentor(resolved_vo_list)

            # Storage arrays travel as kwargs — they're state, not API.
            res_dto, res_want, res_have = await self.__mentor_repository.upsert_mentor(
                db, profile_dto,
                want_tags=new_want,
                have_tags=new_have,
                experiences=column_payload,
                is_mentor=new_is_mentor,
            )

            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(
                db, res_dto, language=language, want_tags=res_want,
            )
            await self.__hydrate_buckets(db, res_vo, res_want, res_have, language)
            return res_vo
        except Exception as e:
            log.error(f'upsert_mentor_profile error: %s', str(e))
            err_msg = getattr(e, 'msg', 'upsert mentor profile response failed')
            # raise_http_exception preserves ClientException as 400; other
            # failures still surface as 500 via ServerException.
            raise_http_exception(e, msg=err_msg)

    async def get_mentor_profile_by_id(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        try:
            row = await self.__mentor_repository.get_mentor_profile_by_id(db, user_id)
            if row is None:
                raise NotFoundException(msg=f"No such user with id: {user_id}")
            mentor_dto, want_tags, have_tags = row
            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(
                db, mentor_dto, language=language, want_tags=want_tags,
            )
            await self.__hydrate_buckets(db, res_vo, want_tags, have_tags, language)
            return res_vo
        except Exception as e:
            log.error(f'get_mentor_profile_by_id error: %s', str(e))
            err_msg = getattr(e, 'msg', 'get mentor profile response failed')
            raise_http_exception(e, msg=err_msg)

    async def __hydrate_buckets(
        self,
        db: AsyncSession,
        vo: MentorProfileVO,
        want_tags: List[str],
        have_tags: List[str],
        language: str,
    ) -> None:
        # Best-effort: hydration failure shouldn't fail the whole profile read.
        # Empty buckets ([]) are explicit on the wire so the frontend can
        # distinguish "user has none" from "field absent".
        try:
            buckets = await self.__tag_service.hydrate_buckets(
                db,
                want_tags=want_tags,
                have_tags=have_tags,
                language=language,
            )
        except Exception as e:
            log.warning("hydrate buckets failed for user %s: %s", vo.user_id, e)
            buckets = {
                'want_position': [], 'want_skill': [], 'want_topic': [],
                'have_skill': [], 'have_topic': [],
            }
        vo.want_position = buckets['want_position']
        vo.want_skill = buckets['want_skill']
        vo.want_topic = buckets['want_topic']
        vo.have_skill = buckets['have_skill']
        vo.have_topic = buckets['have_topic']
