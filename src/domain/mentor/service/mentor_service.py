from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException, ServerException, raise_http_exception
from src.domain.mentor.model.mentor_model import MentorProfileDTO, MentorProfileVO
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.outbox.dao.outbox_message_repository import OutboxMessageRepository
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService
from src.domain.user.service.profile_service import ProfileService
from src.config.constant import EventType, AggregateType
import logging

log = logging.getLogger(__name__)

class MentorService:
    def __init__(self, mentor_repository: MentorRepository, profile_repository: ProfileRepository,
                 interest_service: InterestService, profession_service: ProfessionService, profile_service: ProfileService,
                 outbox_message_repository: OutboxMessageRepository):
        self.__mentor_repository: MentorRepository = mentor_repository
        self.__interest_service: InterestService = interest_service
        self.__profession_service: ProfessionService = profession_service
        self.__profile_repository: ProfileRepository = profile_repository
        self.__profile_service: ProfileService = profile_service
        self.__outbox_repository: OutboxMessageRepository = outbox_message_repository

    async def upsert_mentor_profile(
        self, db: AsyncSession, profile_dto: MentorProfileDTO
    ) -> MentorProfileVO:
        try:
            existing = await self.__mentor_repository.get_mentor_profile_by_id(db, profile_dto.user_id)
            event_type = EventType.USER_UPDATED.value if existing else EventType.USER_CREATED.value

            res_dto: MentorProfileDTO = await self.__mentor_repository.upsert_mentor(
                db, profile_dto
            )
            
            if res_dto.is_mentor:
                await self.__outbox_repository.save_message(
                    db=db,
                    aggregate_id=str(profile_dto.user_id),
                    aggregate_type=AggregateType.PROFILES,
                    event_type=event_type,
                    payload=profile_dto.model_dump(mode="json"),
                )

            await db.commit()

            res_vo: MentorProfileVO = (
                await self.__profile_service.convert_to_mentor_profile_vo(
                    db, res_dto, language=profile_dto.language
                )
            )
            return res_vo

        except Exception as e:
            await db.rollback()
            log.error(f'upsert_mentor_profile error: %s', str(e))
            err_msg = getattr(e, 'msg', 'upsert mentor profile response failed')
            if isinstance(e, ServerException):
                raise e
            raise ServerException(msg=err_msg)

    async def get_mentor_profile_by_id(self, db: AsyncSession, user_id: int, language: str) \
            -> MentorProfileVO:
        try:
            mentor_dto: MentorProfileDTO = await self.__mentor_repository.get_mentor_profile_by_id(db, user_id)
            if mentor_dto is None:
                raise NotFoundException(msg=f"No such user with id: {user_id}")
            return await self.__profile_service.convert_to_mentor_profile_vo(db, mentor_dto, language=language)
        except Exception as e:
            log.error(f'get_mentor_profile_by_id error: %s', str(e))
            err_msg = getattr(e, 'msg', 'get mentor profile response failed')
            raise_http_exception(e, msg=err_msg)
