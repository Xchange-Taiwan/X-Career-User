from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException, ServerException, raise_http_exception
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService
from src.domain.user.service.profile_service import ProfileService
from src.config.constant import TagIntent, TagKind
from src.domain.user.model.tag_model import (
    UserTagBucketsInputDTO,
    UserTagBucketsVO,
    UserTagsUpsertDTO,
)
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

    async def __hydrate_user_tags(
        self, db: AsyncSession, vo: MentorProfileVO, user_id: int
    ) -> None:
        # Best-effort: hydration failure shouldn't fail the whole profile read.
        try:
            tag_list = await self.__tag_service.list_user_tags(db, user_id)
            vo.user_tags = UserTagBucketsVO.from_flat(tag_list.user_tags)
        except Exception as e:
            log.warning("hydrate user_tags failed for user %s: %s", user_id, e)
            vo.user_tags = UserTagBucketsVO()

    async def upsert_mentor_profile(self, db: AsyncSession, profile_dto: MentorProfileDTO) -> MentorProfileVO:
        try:
            res_dto: MentorProfileDTO = await self.__mentor_repository.upsert_mentor(db, profile_dto)
            # Run tag fan-out after legacy upsert so the downstream SQS notify
            # re-reads a consistent snapshot.
            if profile_dto.user_tags is not None:
                await self.__write_user_tag_buckets(
                    db, res_dto.user_id, profile_dto.user_tags, profile_dto.language
                )
            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(db, res_dto, language=profile_dto.language)
            await self.__hydrate_user_tags(db, res_vo, res_dto.user_id)
            return res_vo
        except Exception as e:
            log.error(f'upsert_mentor_profile error: %s', str(e))
            err_msg = getattr(e, 'msg', 'upsert mentor profile response failed')
            raise ServerException(msg=err_msg)

    async def __write_user_tag_buckets(
        self,
        db: AsyncSession,
        user_id: int,
        buckets: UserTagBucketsInputDTO,
        profile_language: Optional[str],
    ) -> None:
        # None = leave bucket alone, [] = clear, [...] = replace contents.
        bucket_map = (
            ('want_skills',    TagKind.SKILL,    TagIntent.WANT),
            ('offer_skills',   TagKind.SKILL,    TagIntent.OFFER),
            ('want_topics',    TagKind.TOPIC,    TagIntent.WANT),
            ('offer_topics',   TagKind.TOPIC,    TagIntent.OFFER),
            ('want_positions', TagKind.POSITION, TagIntent.WANT),
        )
        for bucket_name, kind, intent in bucket_map:
            subject_groups = getattr(buckets, bucket_name)
            if subject_groups is None:
                continue
            await self.__tag_service.replace_user_tags(
                db,
                user_id,
                UserTagsUpsertDTO(
                    kind=kind,
                    intent=intent,
                    subject_groups=subject_groups,
                    language=profile_language,
                ),
            )

    async def get_mentor_profile_by_id(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        try:
            mentor_dto: MentorProfileDTO = await self.__mentor_repository.get_mentor_profile_by_id(db, user_id)
            if mentor_dto is None:
                raise NotFoundException(msg=f"No such user with id: {user_id}")
            res_vo: MentorProfileVO = await self.__profile_service.convert_to_mentor_profile_vo(db, mentor_dto, language=language)
            await self.__hydrate_user_tags(db, res_vo, user_id)
            return res_vo
        except Exception as e:
            log.error(f'get_mentor_profile_by_id error: %s', str(e))
            err_msg = getattr(e, 'msg', 'get mentor profile response failed')
            raise_http_exception(e, msg=err_msg)
